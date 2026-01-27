import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Phone, Mail, MapPin, Briefcase, TrendingUp, AlertTriangle, Calendar, User, Clock, ArrowRight, Plus } from 'lucide-react';
// Importamos o Modal que você criou
import ModalNovoParceiro from './ModalNovoParceiro';

const AbaParceiros = () => {
  const [parceiroSelecionado, setParceiroSelecionado] = useState(null);
  const [parceiros, setParceiros] = useState([]);
  const [loading, setLoading] = useState(true);
  const [mostrarModal, setMostrarModal] = useState(false); // Controle do Modal

  // --- 1. BUSCA INICIAL DE DADOS ---
  useEffect(() => {
    carregarParceiros();
  }, []);

  const carregarParceiros = () => {
    axios.get('https://prevision-backend.onrender.com/api/parceiros/')
      .then(response => {
        setParceiros(response.data);
        setLoading(false);
      })
      .catch(erro => console.error("Erro ao buscar parceiros:", erro));
  };

  // --- 2. FUNÇÃO QUANDO CRIA UM NOVO PARCEIRO ---
  const aoAdicionarParceiro = (novoParceiro) => {
    setParceiros([novoParceiro, ...parceiros]); // Adiciona no topo da lista
    setParceiroSelecionado(novoParceiro); // Já seleciona ele na tela
  };

  // --- 3. FUNÇÃO NOVA: REGISTRAR PONTOS (Venda/Indicação) ---
  const registrarMovimentacao = async () => {
    if (!parceiroSelecionado) return;

    // Pergunta simples (para o MVP)
    const pontos = prompt("Quantos pontos essa ação vale? (Indicação = 0.7; Venda = 1.0)", "0.7");
    
    if (pontos) {
      try {
        // Manda para o Django calcular
        const response = await axios.post(`https://prevision-backend.onrender.com/api/parceiros/${parceiroSelecionado.id}/registrar_indicacao/`, {
          pontos: pontos
        });
        
        const parceiroAtualizado = response.data;
        
        // Atualiza a lista geral (troca o antigo pelo novo)
        setParceiros(parceiros.map(p => p.id === parceiroAtualizado.id ? parceiroAtualizado : p));
        
        // Atualiza o detalhe que você está vendo agora
        setParceiroSelecionado(parceiroAtualizado);
        
        alert(`Sucesso! Score atualizado para ${parceiroAtualizado.score_atual}`);
      } catch (error) {
        console.error("Erro ao pontuar:", error);
        alert("Erro ao registrar pontuação. Verifique se o Backend está rodando.");
      }
    }
  };

  // --- 4. CÁLCULOS VISUAIS (Barra de Progresso) ---
  const niveis = { bronze: 1.7, prata: 2.4, ouro: 3.4, diamante: 6.1 };

  const getProgresso = (score) => {
    const s = parseFloat(score);
    let proximoNivel = 10; let nomeProximo = "Max"; let base = 0;

    if (s < niveis.bronze) { proximoNivel = niveis.bronze; nomeProximo = "Bronze"; base = 0; }
    else if (s < niveis.prata) { proximoNivel = niveis.prata; nomeProximo = "Prata"; base = niveis.bronze; }
    else if (s < niveis.ouro) { proximoNivel = niveis.ouro; nomeProximo = "Ouro"; base = niveis.prata; }
    else if (s < niveis.diamante) { proximoNivel = niveis.diamante; nomeProximo = "Diamante"; base = niveis.ouro; }
    else { return { pct: 100, label: "Topo Alcançado!" }; }

    const pct = ((s - base) / (proximoNivel - base)) * 100;
    const falta = (proximoNivel - s).toFixed(1);
    
    return { pct, label: `Faltam ${falta} pts para ${nomeProximo}` };
  };

  return (
    <div className="flex h-full bg-gray-50 overflow-hidden relative">
      
      {/* --- O MODAL (Só aparece se mostrarModal for true) --- */}
      {mostrarModal && (
        <ModalNovoParceiro 
          aoFechar={() => setMostrarModal(false)} 
          aoSalvar={aoAdicionarParceiro} 
        />
      )}

      {/* --- COLUNA ESQUERDA: LISTA --- */}
      <div className="w-1/3 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-4 border-b border-gray-100 bg-white sticky top-0 z-10 space-y-3">
          <div className="flex justify-between items-center">
            <h2 className="text-lg font-bold text-gray-800 flex items-center gap-2">
              <Briefcase size={20} className="text-blue-600"/> Parceiros ({parceiros.length})
            </h2>
          </div>
          
          {/* BOTÃO AZUL DE ADICIONAR */}
          <button 
            onClick={() => setMostrarModal(true)}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 rounded-lg flex items-center justify-center gap-2 font-medium transition shadow-sm"
          >
            <Plus size={18} /> Adicionar Parceiro
          </button>
        </div>
        
        <div className="overflow-y-auto flex-1 p-2 space-y-2 scrollbar-thin">
          {loading ? (
            <p className="text-center text-gray-400 mt-10">Carregando dados...</p>
          ) : parceiros.map((p) => {
            const alerta = p.dias_sem_indicar >= 25; 

            return (
              <div 
                key={p.id} 
                onClick={() => setParceiroSelecionado(p)}
                className={`p-4 rounded-xl cursor-pointer border transition-all hover:shadow-md ${
                  parceiroSelecionado?.id === p.id ? 'bg-blue-50 border-blue-500 ring-1 ring-blue-500' : 'bg-white border-gray-100'
                }`}
              >
                <div className="flex justify-between items-start">
                  <span className="font-bold text-gray-700">{p.empresa}</span>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider ${
                    p.status === 'Diamante' ? 'bg-cyan-100 text-cyan-700' :
                    p.status === 'Ouro' ? 'bg-yellow-100 text-yellow-700' :
                    p.status === 'Prata' ? 'bg-gray-200 text-gray-600' : 'bg-orange-100 text-orange-700'
                  }`}>
                    {p.status}
                  </span>
                </div>
                <div className="flex justify-between items-end mt-2">
                  <div className="text-xs text-gray-500 flex items-center gap-1"><MapPin size={12}/> {p.cidade}</div>
                  {alerta && (
                    <div className="flex items-center gap-1 text-[10px] font-bold text-red-600 bg-red-50 px-2 py-1 rounded">
                      <Clock size={10} /> {p.dias_sem_indicar} dias off
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* --- COLUNA DIREITA: DETALHES --- */}
      <div className="w-2/3 overflow-y-auto bg-gray-50 p-6 md:p-8">
        {parceiroSelecionado ? (
          <div className="max-w-4xl mx-auto space-y-6 pb-10">
            
            {/* CABEÇALHO DOS DETALHES */}
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
              <div className="flex justify-between items-start">
                <div>
                  <h1 className="text-3xl font-bold text-gray-800">{parceiroSelecionado.empresa}</h1>
                  <div className="flex items-center gap-4 mt-3 text-sm text-gray-500">
                    <span className="flex items-center gap-1 bg-gray-100 px-2 py-1 rounded"><User size={14}/> {parceiroSelecionado.contato_nome}</span>
                    <span className="flex items-center gap-1"><Calendar size={14}/> Última indicação: <strong>{parceiroSelecionado.ultima_indicacao}</strong></span>
                  </div>
                </div>
                
                <div className="flex flex-col items-end gap-2">
                  <div className="text-right">
                    <p className="text-xs text-gray-400 uppercase font-bold tracking-widest">Score Atual</p>
                    <p className="text-5xl font-extrabold text-blue-600 tracking-tighter">{parceiroSelecionado.score_atual}</p>
                  </div>
                  
                  {/* BOTÃO VERDE DE LANÇAR VENDA */}
                  <button 
                    onClick={registrarMovimentacao}
                    className="bg-green-600 hover:bg-green-700 text-white text-xs font-bold py-2 px-4 rounded-lg flex items-center gap-2 shadow-sm transition-all transform active:scale-95"
                  >
                    <TrendingUp size={14} /> Lançar Venda/Indicação
                  </button>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              
              {/* CARD PROGRESSO */}
              <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                <h3 className="font-bold text-gray-700 flex items-center gap-2 mb-4">
                  <TrendingUp size={18} className="text-green-500"/> Progresso
                </h3>
                <div className="flex justify-between text-xs font-bold text-gray-500 uppercase mb-2">
                  <span>{parceiroSelecionado.status}</span>
                  <span className="text-blue-600">{getProgresso(parceiroSelecionado.score_atual).label}</span>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-3">
                  <div 
                    className="bg-gradient-to-r from-blue-500 to-cyan-400 h-3 rounded-full shadow-[0_0_10px_rgba(59,130,246,0.3)]" 
                    style={{ width: `${getProgresso(parceiroSelecionado.score_atual).pct}%` }}
                  ></div>
                </div>
              </div>

              {/* CARD PREVISÃO (INTELIGÊNCIA DO DJANGO) */}
              {(() => {
                const diasPassados = parceiroSelecionado.dias_sem_indicar;
                const diasRestantes = 30 - diasPassados;
                const multa = parceiroSelecionado.multa_estimada;
                const novoScore = parceiroSelecionado.score_futuro;
                
                const isLate = diasRestantes <= 0;
                const isWarning = diasRestantes <= 10 && !isLate;
                
                const borderClass = isLate ? 'border-red-200' : isWarning ? 'border-orange-200' : 'border-green-100';
                const bgIcon = isLate ? 'bg-red-50 text-red-600' : isWarning ? 'bg-orange-50 text-orange-600' : 'bg-green-50 text-green-600';

                return (
                  <div className={`bg-white p-6 rounded-2xl shadow-sm border ${borderClass} relative overflow-hidden group`}>
                    <div className={`absolute right-0 top-0 w-24 h-24 rounded-bl-full -mr-6 -mt-6 transition-transform group-hover:scale-110 ${
                        isLate ? 'bg-red-50' : isWarning ? 'bg-orange-50' : 'bg-green-50'
                    }`}></div>
                    
                    <h3 className="font-bold text-gray-700 flex items-center gap-2 mb-4 relative z-10">
                      <Calendar size={18} className={isLate ? "text-red-500" : isWarning ? "text-orange-500" : "text-green-500"}/> 
                      Previsão de Queda
                    </h3>

                    <div className="flex items-center gap-4 relative z-10">
                      <div className={`p-3 rounded-xl border ${bgIcon} border-opacity-20`}>
                        {isLate ? <AlertTriangle size={24} /> : <Clock size={24} />}
                      </div>
                      
                      {parceiroSelecionado.status === 'Bronze' ? (
                          <div>
                            <p className="text-sm text-gray-600">Categoria <strong className="text-orange-700">Bronze</strong></p>
                            <p className="text-xs text-gray-500 mt-1">Isenta de punição por inatividade.</p>
                          </div>
                      ) : (
                          <div className="w-full">
                            <p className="text-xs text-gray-500 mb-1 font-medium">
                                Dias restantes: <span className={isWarning || isLate ? "text-red-600 font-bold" : "text-gray-800"}>{Math.max(0, diasRestantes)}</span>
                            </p>
                            
                            <div className="flex items-center gap-2 bg-gray-50 p-2 rounded-lg border border-gray-100">
                                <span className="text-sm font-bold text-gray-400 line-through decoration-red-400 decoration-2">
                                    {parceiroSelecionado.score_atual}
                                </span>
                                <ArrowRight size={14} className="text-gray-400"/>
                                <span className={`text-2xl font-extrabold ${isLate ? 'text-red-600' : 'text-gray-800'}`}>
                                    {novoScore}
                                </span>
                            </div>
                            <p className="text-[10px] text-gray-400 mt-1 text-right">
                                Penalidade prevista: -{multa} pts
                            </p>
                          </div>
                      )}
                    </div>
                  </div>
                );
              })()}
            </div>

            {/* SERVIÇOS (TAGS) */}
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
              <h3 className="font-bold text-gray-700 mb-6 flex items-center gap-2"><Briefcase size={18} className="text-gray-400"/> Atividades Realizadas</h3>
              <div className="flex flex-wrap gap-2">
                {parceiroSelecionado.servicos_lista && parceiroSelecionado.servicos_lista.map((servico) => (
                  <div key={servico} className="px-3 py-2 rounded-lg text-xs font-semibold border bg-blue-50 text-blue-700 border-blue-200 shadow-sm">
                    ✅ {servico}
                  </div>
                ))}
                {(!parceiroSelecionado.servicos_lista || parceiroSelecionado.servicos_lista.length === 0) && (
                   <p className="text-sm text-gray-400 italic">Nenhum serviço cadastrado.</p>
                )}
              </div>
            </div>

          </div>
        ) : (
          <div className="h-full flex items-center justify-center text-gray-400">Selecione um parceiro ao lado</div>
        )}
      </div>
    </div>
  );
};

export default AbaParceiros;