import ClientList from '../../components/ClientList';

export default function ClientsPage() {
  return (
    <main className="p-8 max-w-7xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Clients</h1>
      <ClientList />
    </main>
  );
}
