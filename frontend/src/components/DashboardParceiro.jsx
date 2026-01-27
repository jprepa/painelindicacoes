import React, { useState, useEffect } from 'react';

const DashboardParceiro = () => {
  // Estados para simular os dados (no sistema real, viriam do Banco de Dados)
  const [indicacoes, setIndicacoes] = useState(2); // Exemplo inicial
  const [vendas, setVendas] = useState(1);         // Exemplo inicial
  const [score, setScore] = useState(0);

  // Regras da sua tabela
  const niveis = {
    bronze: 1.7,
    prata: 2.4,
    ouro: 3.4,
    diamante: 6.1
  };

  // Recalcula o score sempre que muda indicações ou vendas
  useEffect(() => {
    // Fórmula: (Indicação * 0.7) + (Vendas * 1)
    const novoScore = (indicacoes * 0.7) + (vendas * 1);
    setScore(novoScore.toFixed(1)); // Arredonda para 1 casa decimal
  }, [indicacoes, vendas]);

  // Função para determinar o selo e a cor
  const getStatus = () => {
    if (score >= niveis.diamante) return { nome: 'DIAMANTE', cor: 'bg-blue-500', texto: 'text-blue-600' };
    if (score >= niveis.ouro) return { nome: 'OURO', cor: 'bg-yellow-500', texto: 'text-yellow-600' };
    if (score >= niveis.prata) return { nome: 'PRATA', cor: 'bg-gray-400', texto: 'text-gray-500' };
    if (score >= niveis.bronze) return { nome: 'BRONZE', cor: 'bg-orange-600', texto: 'text-orange-700' };
    return { nome: 'SEM SELO', cor: 'bg-gray-200', texto: 'text-gray-400' };
  };

  const status = getStatus();

  // Calcula % para a barra de progresso (baseado no alvo máximo de 7 pontos para visualização)
  const progresso = Math.min((score / 7) * 100, 100);

  return (
    <div className="p-8 max-w-md mx-auto bg-white rounded-xl shadow-lg border border-gray-100 font-sans">
      {/* 1. Cabeçalho com o Selo Atual */}
      <div className="text-center mb-8">
        <h2 className="text-gray-500 text-sm font-bold uppercase tracking-wide">Sua Categoria Atual</h2>
        <div className={`mt-2 inline-block px-6 py-2 rounded-full text-white font-bold text-2xl shadow-md ${status.cor}`}>
          {status.nome} 🏆
        </div>
        <p className="mt-4 text-4xl font-extrabold text-gray-800">{score} <span className="text-lg text-gray-400">pontos</span></p>
      </div>

      {/* 2. Barra de Progresso Visual */}
      <div className="mb-8">
        <div className="flex justify-between text-xs text-gray-400 mb-1">
          <span>Início</span>
          <span>Diamante (6.1)</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-4">
          <div 
            className={`h-4 rounded-full transition-all duration-500 ${status.cor}`} 
            style={{ width: `${progresso}%` }}
          ></div>
        </div>
        <p className="text-xs text-center mt-2 text-gray-500">
          Próximo nível em breve... Mantenha o ritmo!
        </p>
      </div>

      {/* 3. Simulador (Painel de Controle) */}
      <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
        <h3 className="text-sm font-bold text-gray-700 mb-4">📢 Simulador de Performance</h3>
        
        <div className="flex gap-4 mb-4">
          <div className="flex-1">
            <label className="block text-xs font-bold text-gray-500 mb-1">Indicações (0.7 pts)</label>
            <input 
              type="number" 
              value={indicacoes}
              onChange={(e) => setIndicacoes(Number(e.target.value))}
              className="w-full p-2 border rounded text-center text-lg font-bold text-gray-700"
            />
          </div>
          <div className="flex-1">
            <label className="block text-xs font-bold text-gray-500 mb-1">Vendas (1.0 pts)</label>
            <input 
              type="number" 
              value={vendas}
              onChange={(e) => setVendas(Number(e.target.value))}
              className="w-full p-2 border rounded text-center text-lg font-bold text-gray-700"
            />
          </div>
        </div>
        
        <p className="text-xs text-gray-500 italic text-center">
          *Altere os números acima para ver seu selo mudar em tempo real.
        </p>
      </div>
    </div>
  );
};

export default DashboardParceiro;