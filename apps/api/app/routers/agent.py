"""
AI Agent Chat — Claude + database tools, citations.
Answers natural language questions about a client's financial data.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime
from decimal import Decimal
import httpx, json
from app.database import get_db
from app.models import Client, Account, JournalEntry, JournalLine, Invoice, Transaction
from app.auth import AuthUser, get_current_user
from app.config import get_settings

router = APIRouter(prefix="/api/v1/agent", tags=["agent"])
settings = get_settings()

# ─── Schemas ──────────────────────────────────────────────────────────────────

class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class AgentRequest(BaseModel):
    client_id: int
    question: str
    history: list[Message] = []


class ToolResult(BaseModel):
    tool: str
    sql: str
    rows_returned: int
    data: list[dict]


class AgentResponse(BaseModel):
    answer: str
    citations: list[str]  # e.g. ["Invoices: #123", "Account: 4000"]
    tools_used: list[ToolResult]
    generated_at: datetime


# ─── Database Tool ─────────────────────────────────────────────────────────────

def run_db_query(db: Session, sql: str) -> tuple[list[dict], str]:
    """
    Execute a SELECT query and return results.
    """
    try:
        result = db.execute(sql)
        rows = [dict(row._mapping) for row in result]
        # Convert Decimals and dates to JSON-serializable
        for row in rows:
            for k, v in row.items():
                if isinstance(v, Decimal):
                    row[k] = float(v)
                elif isinstance(v, datetime):
                    row[k] = v.isoformat()
        return rows, ""
    except Exception as e:
        return [], str(e)


# ─── Tool System ───────────────────────────────────────────────────────────────

AVAILABLE_TOOLS = {
    "sql_query": {
        "description": "Execute a SQL SELECT query against the BPO Nexus database. Returns up to 50 rows.",
        "parameters": {
            "type": "object",
            "properties": {
                "sql": {
                    "type": "string",
                    "description": "A SELECT SQL query. Use table names: clients, accounts, journal_entries, journal_lines, invoices, bank_transactions, transactions.",
                }
            },
            "required": ["sql"],
        },
    },
    "get_client_summary": {
        "description": "Get a quick summary of a client: name, country, industry, number of accounts, recent journal entries.",
        "parameters": {
            "type": "object",
            "properties": {
                "client_id": {"type": "integer"},
            },
            "required": ["client_id"],
        },
    },
    "get_pnl_summary": {
        "description": "Get P&L summary for a client for a specific period.",
        "parameters": {
            "type": "object",
            "properties": {
                "client_id": {"type": "integer"},
                "year": {"type": "integer"},
                "month": {"type": "integer"},
            },
            "required": ["client_id"],
        },
    },
}


def call_tool(tool_name: str, params: dict, db: Session) -> dict:
    """Execute a named tool and return the result."""
    if tool_name == "sql_query":
        rows, error = run_db_query(db, params["sql"])
        return {"rows_returned": len(rows), "data": rows[:50], "error": error}

    elif tool_name == "get_client_summary":
        client_id = params["client_id"]
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            return {"error": f"Client {client_id} not found"}

        n_accounts = db.query(Account).filter(Account.client_id == client_id).count()
        n_entries = db.query(JournalEntry).filter(JournalEntry.client_id == client_id).count()

        return {
            "client_id": client.id,
            "name": client.name,
            "country": client.country,
            "industry": client.industry,
            "n_accounts": n_accounts,
            "n_journal_entries": n_entries,
        }

    elif tool_name == "get_pnl_summary":
        from app.routers.journal import get_period_totals, net_balance
        client_id = params["client_id"]
        year = params.get("year", datetime.now().year)
        month = params.get("month", datetime.now().month)

        from app.routers.journal import parse_date_range
        start, end = parse_date_range(year, month)
        totals = get_period_totals(db, client_id, start, end)

        revenue = sum(
            abs(net_balance(code, d["account_type"], d["debit"], d["credit"]))
            for code, d in totals.items() if d["account_type"] == "revenue"
        )
        expenses = sum(
            abs(net_balance(code, d["account_type"], d["debit"], d["credit"]))
            for code, d in totals.items() if d["account_type"] == "expense"
        )

        return {
            "period": f"{year}-{month:02d}",
            "revenue": float(revenue),
            "expenses": float(expenses),
            "net_profit": float(revenue - expenses),
        }

    return {"error": f"Unknown tool: {tool_name}"}


# ─── Agent Loop ───────────────────────────────────────────────────────────────

MAX_TOOL_CALLS = 5


async def run_agent_loop(
    question: str,
    history: list[Message],
    client_id: int,
    db: Session,
) -> tuple[str, list[ToolResult], list[str]]:
    """
    Run the agent: send question to Claude with DB tools, let it call tools,
    return the final answer with citations.
    """
    system_prompt = f"""You are a financial data analyst AI agent for BPO Nexus.
You have access to database tools to answer questions about a client's financial data.

Available tools:
{json.dumps(AVAILABLE_TOOLS, indent=2)}

Rules:
1. Only use sql_query for custom queries — prefer specific tools when possible
2. Always cite your sources: mention table names and specific IDs/numbers
3. Keep answers concise and professional (under 200 words)
4. If data is not available, say so — do not make up numbers
5. Think step by step before calling tools

You are answering questions about client_id={client_id}."""

    messages = [{"role": "system", "content": system_prompt}]
    for msg in history[-10:]:  # Last 10 messages
        messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": question})

    tools_used = []
    citations = []
    tool_calls = 0

    async with httpx.AsyncClient(timeout=120.0) as http:
        while tool_calls < MAX_TOOL_CALLS:
            resp = await http.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": settings.claude_api_key,
                    "anthropic-version": "2023-06-01",
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 1024,
                    "messages": messages,
                    "tools": [
                        {"name": name, "description": desc["description"], "input_schema": desc["parameters"]}
                        for name, desc in AVAILABLE_TOOLS.items()
                    ],
                },
            )

            if resp.status_code != 200:
                raise HTTPException(status_code=502, detail=f"Claude API error: {resp.text[:200]}")

            data = resp.json()
            assistant_msg = data["content"][0]
            messages.append({"role": "assistant", "content": assistant_msg["text"] if assistant_msg["type"] == "text" else ""})

            # Check for tool use
            tool_results_content = []
            for block in data.get("content", []):
                if block.get("type") == "tool_use":
                    tool_calls += 1
                    tool_name = block["name"]
                    tool_input = block["input"]

                    # Execute tool
                    result = call_tool(tool_name, tool_input, db)
                    tool_result_id = block["id"]

                    # Extract SQL for logging
                    sql = tool_input.get("sql", "") if tool_name == "sql_query" else ""

                    if "error" in result:
                        result_text = f"Error: {result['error']}"
                    else:
                        result_text = json.dumps(result)[:500]

                    tool_results_content.append({
                        "type": "tool_result",
                        "tool_use_id": tool_result_id,
                        "content": result_text,
                    })

                    tools_used.append(ToolResult(
                        tool=tool_name,
                        sql=sql,
                        rows_returned=result.get("rows_returned", 0),
                        data=result.get("data", []),
                    ))

                    # Add citation
                    if tool_name == "sql_query" and sql:
                        citations.append(f"Query: {sql[:80]}...")
                    elif tool_name == "get_client_summary":
                        citations.append(f"Client: {result.get('name', 'N/A')}")
                    elif tool_name == "get_pnl_summary":
                        citations.append(f"P&L {result.get('period', '')}")

            if not tool_results_content:
                # No tools called — this is the final answer
                answer = assistant_msg.get("text", "")
                return answer.strip(), tools_used, citations

            messages.extend(tool_results_content)

        # Max tool calls reached
        return ("I needed more than 5 tool calls to answer that question. "
                "Try being more specific."), tools_used, citations


# ─── Route ───────────────────────────────────────────────────────────────────

@router.post("/chat", response_model=AgentResponse)
async def agent_chat(
    data: AgentRequest,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user),
):
    """
    Ask a natural language question about a client's financial data.
    Claude will use database tools to answer with citations.
    """
    # Verify access
    client = db.query(Client).filter(
        Client.id == data.client_id,
        Client.agency_id == current_user.agency_id,
    ).first()
    if not client:
        raise HTTPException(status_code=403, detail="Client not found")

    answer, tools_used, citations = await run_agent_loop(
        question=data.question,
        history=data.history,
        client_id=data.client_id,
        db=db,
    )

    return AgentResponse(
        answer=answer,
        citations=citations,
        tools_used=tools_used,
        generated_at=datetime.utcnow(),
    )
