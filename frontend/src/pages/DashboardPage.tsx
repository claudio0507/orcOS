export function DashboardPage() {
  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-4">Dashboard orcOS</h1>
      <p className="text-gray-600 mb-8">Bem-vindo ao sistema de orçamentos e precificação.</p>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="p-6 bg-white rounded-lg shadow border border-gray-100">
          <h2 className="font-semibold text-lg mb-2">Orçamentos</h2>
          <p className="text-2xl font-bold text-blue-600">0</p>
        </div>
        <div className="p-6 bg-white rounded-lg shadow border border-gray-100">
          <h2 className="font-semibold text-lg mb-2">Fichas Técnicas</h2>
          <p className="text-2xl font-bold text-green-600">0</p>
        </div>
        <div className="p-6 bg-white rounded-lg shadow border border-gray-100">
          <h2 className="font-semibold text-lg mb-2">Alertas de Auditoria</h2>
          <p className="text-2xl font-bold text-red-500">OK</p>
        </div>
      </div>

      <div className="mt-12">
        <h3 className="text-xl font-semibold mb-4">Orçamentos Recentes</h3>
        <div className="bg-white rounded-lg shadow overflow-hidden border border-gray-200">
          <table className="w-full text-left">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-3 text-sm font-medium text-gray-500">ID</th>
                <th className="px-6 py-3 text-sm font-medium text-gray-500">Título</th>
                <th className="px-6 py-3 text-sm font-medium text-gray-500">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              <tr>
                <td className="px-6 py-4 text-sm text-gray-400 italic" colSpan={3}>Nenhum orçamento encontrado.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
