import ClientList from '../../components/ClientList';
import TaskQueue from '../../components/TaskQueue';

export default function Dashboard() {
  return (
    <main className="p-8 max-w-7xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Agency Command Centre</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <ClientList />
        <TaskQueue />
      </div>
    </main>
  );
}
