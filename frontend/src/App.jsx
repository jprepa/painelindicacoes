import React, { useState } from 'react';
import { LayoutDashboard, Users, Trophy, Sheet } from 'lucide-react';

// Importando seus componentes
import AbaParceiros from './components/AbaParceiros';
import AbaQualificacao from './components/AbaQualificacao'; 
import AbaBeneficios from './components/AbaBeneficios';

function App() {
  const [abaAtiva, setAbaAtiva] = useState('parceiros');

  // Função que decide o que mostrar na tela principal
  const renderConteudo = () => {
    switch(abaAtiva) {
      case 'parceiros': 
        return <AbaParceiros />;
case 'beneficios': 
  return <AbaBeneficios />;
      case 'qualificacao': 
        return <AbaQualificacao />;
      case 'dashboards': 
        return (
          <div className="h-full flex flex-col items-center justify-center bg-gray-50 text-gray-400">
            <LayoutDashboard size={48} className="mb-4 text-blue-500 opacity-50" />
            <p className="text-xl font-semibold">Dashboards de BI</p>
            <p className="text-sm">Em breve aqui...</p>
          </div>
        );
      default: 
        return <AbaParceiros />;
    }
  };

  return (
    <div className="flex h-screen bg-gray-100 font-sans overflow-hidden">
      
      {/* --- SIDEBAR LATERAL --- */}
      <div className="w-64 bg-slate-900 text-white flex flex-col shadow-2xl z-20 shrink-0">
        <div className="p-6 border-b border-slate-800">
          <h1 className="font-light text-white">
            Parceiros<span className="ftext-xl font-bold bg-gradient-to-r from-blue-400 to-cyan-300 bg-clip-text text-transparent">Prevision</span>
          </h1>
        </div>

        <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
          
          <button 
            onClick={() => setAbaAtiva('parceiros')}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
              abaAtiva === 'parceiros' ? 'bg-blue-600 text-white shadow-lg' : 'text-slate-400 hover:bg-slate-800 hover:text-white'
            }`}
          >
            <Users size={20} /> Parceiros & Indicações
          </button>

          <button 
            onClick={() => setAbaAtiva('beneficios')}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
              abaAtiva === 'beneficios' ? 'bg-blue-600 text-white shadow-lg' : 'text-slate-400 hover:bg-slate-800 hover:text-white'
            }`}
          >
            <Trophy size={20} /> Tabela de Benefícios
          </button>

          <button 
            onClick={() => setAbaAtiva('qualificacao')}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
              abaAtiva === 'qualificacao' ? 'bg-purple-600 text-white shadow-lg' : 'text-slate-400 hover:bg-slate-800 hover:text-white'
            }`}
          >
            <Sheet size={20} /> Agente Qualificação
          </button>

          <button 
            onClick={() => setAbaAtiva('dashboards')}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
              abaAtiva === 'dashboards' ? 'bg-blue-600 text-white shadow-lg' : 'text-slate-400 hover:bg-slate-800 hover:text-white'
            }`}
          >
            <LayoutDashboard size={20} /> Dashboards (BI)
          </button>
        </nav>

        <div className="p-4 border-t border-slate-800 text-xs text-slate-500 text-center">
          v1.0 Beta
        </div>
      </div>

      {/* --- CONTEÚDO PRINCIPAL --- */}
      <div className="flex-1 relative overflow-hidden bg-gray-50">
        {renderConteudo()}
      </div>

    </div>
  );
}

export default App;