import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Phone, MapPin, Briefcase, TrendingUp, Filter, Calendar, User, Clock, ArrowRight, Plus, History, CheckCircle, Edit2 } from 'lucide-react';
import ModalNovoParceiro from './ModalNovoParceiro';

const AbaParceiros = () => {
  const [parceiroSelecionado, setParceiroSelecionado] = useState(null);
  const [parceiros, setParceiros] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // --- NOVO: ESTADOS PARA EDIÇÃO ---
  const [mostrarModal, setMostrarModal] = useState(false);
  const [parceiroParaEditar, setParceiroParaEditar] = useState(null); // Guarda quem será editado

  // --- FILTROS ---
  const [filtroTexto, setFiltroTexto] = useState("");
  const [filtroEstado, setFiltroEstado] = useState("");
  const [filtroServico, setFiltroServico] = useState("");

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

  // --- LÓGICA DE SALVAR (INTELIGENTE: CRIA OU EDITA) ---
  const aoSalvarParceiro = (parceiroAtualizado) => {
    // Verifica se já existe na lista (se tem ID igual)
    const existe = parceiros.find(p => p.id === parceiroAtualizado.id);
    
    if (existe) {
      // É UMA EDIÇÃO: Substitui o antigo pelo novo na lista
      setParceiros(parceiros.map(p => p.id === parceiroAtualizado.id ? parceiroAtualizado : p));
      
      // Se ele estava selecionado na tela, atualiza os detalhes também
      if (parceiroSelecionado?.id === parceiroAtualizado.id) {
        setParceiroSelecionado(parceiroAtualizado);
      }
    } else {
      // É NOVO: Adiciona no topo
      setParceiros([parceiroAtualizado, ...parceiros]);
      setParceiroSelecionado(parceiroAtualizado);
    }
    setMostrarModal(false);
    setParceiroParaEditar(null); // Limpa a memória de edição
  };

  // Abre o modal PREENCHIDO
  const abrirModalEdicao = () => {
    setParceiroParaEditar(parceiroSelecionado);
    setMostrarModal(true);
  }

  // Abre o modal VAZIO
  const abrirModalNovo = () => {
    setParceiroParaEditar(null);
    setMostrarModal(true);
  }

  // --- FUNÇÃO DE PONTUAÇÃO ---
  const registrarMovimentacao = async (tipo) => {
    if (!parceiroSelecionado) return;
    const valorPadrao = tipo === 'Venda' ? "1.0" : "0.7";
    const pontos = prompt(`Quantos pontos para essa ${tipo}?`, valorPadrao);
    
    if (pontos) {
      try {
        const response = await axios.post(`https://prevision-backend.onrender.com/api/parceiros/${parceiroSelecionado.id}/registrar_indicacao/`, {
          pontos: pontos, tipo: tipo
        });
        const atualizado = response.data;
        setParceiros(parceiros.map(p => p.id === atualizado.id ? atualizado : p));
        setParceiroSelecionado(atualizado);
        alert("Pontuação registrada!");
      } catch (error) {
        alert("Erro no servidor.");
      }
    }
  };

  // --- LÓGICA DE FILTRAGEM ---
  const todosEstados = [...new Set(parceiros.flatMap(p => p.estados_lista || []))].sort();
  const todosServicos = [...new Set(parceiros.flatMap(p => p.servicos_lista || []))].sort();

  const parceirosFiltrados = parceiros.filter(p => {
    const matchTexto = p.empresa.toLowerCase().includes(filtroTexto.toLowerCase());
    const matchEstado = filtroEstado ? (p.estados_lista && p.estados_lista.includes(filtroEstado)) : true;
    const matchServico = filtroServico ? (p.servicos_lista && p.servicos_lista.includes(filtroServico)) : true;
    return matchTexto && matchEstado && matchServico;
  });

  // Cálculos Visuais
  const niveis = { bronze: 1.7, prata: 2.4, ouro: 3.4, diamante: 6.1 };
  const getProgresso = (score) => {
    const s = parseFloat(score);
    let proximoNivel = 10; let nomeProximo = "Max"; let base = 0;
    if (s < niveis.bronze) { proximoNivel = niveis.bronze; nomeProximo = "Bronze"; base = 0; }
    else if (s < niveis.prata) { proximoNivel = niveis.prata; nomeProximo = "Prata"; base = niveis.bronze; }
    else if (s < niveis.ouro) { proximoNivel = niveis.ouro; nomeProximo = "Ouro"; base = niveis.prata; }
    else if (s < niveis.diamante) { proximoNivel = niveis.diamante; nomeProximo = "Diamante"; base = niveis.ouro; }
    else { return { pct: 100, label: "Topo!" }; }
    const pct = ((s - base) / (proximoNivel - base)) * 100;
    const falta = (proximoNivel - s).toFixed(1);
    return { pct, label: `Faltam ${falta} para ${nomeProximo}` };
  };

  return (
    <div className="flex h-full bg-gray-50 overflow-hidden relative">
      
      {/* MODAL AGORA RECEBE 'parceiroParaEditar' */}
      {mostrarModal && (
        <ModalNovoParceiro 
          aoFechar={() => setMostrarModal(false)} 
          aoSalvar={aoSalvarParceiro}
          parceiroParaEditar={parceiroParaEditar} 
        />
      )}

      {/* COLUNA ESQUERDA */}
      <div className="w-1/3 bg-white border-r border-gray-200 flex flex-col shadow-lg z-10">
        <div className="p-4 border-b border-gray-100 bg-white space-y-3">
          <div className="flex justify-between items-center mb-2">
            <h2 className="text-lg font-bold text-gray-800 flex items-center gap-2">
              <Briefcase size={20} className="text-blue-600"/> Parceiros ({parceirosFiltrados.length})
            </h2>
          </div>
          
          <div className="space-y-2">
             <input type="text" placeholder="Buscar parceiro..." className="w-full text-sm p-2 border rounded-lg bg-gray-50"
                value={filtroTexto} onChange={e => setFiltroTexto(e.target.value)} />
             <div className="flex gap-2">
                <select className="w-1/2 text-xs p-2 border rounded-lg bg-white" onChange={e => setFiltroEstado(e.target.value)} value={filtroEstado}>
                    <option value="">Todos Estados</option>
                    {todosEstados.map(e => <option key={e} value={e}>{e}</option>)}
                </select>
                <select className="w-1/2 text-xs p-2 border rounded-lg bg-white" onChange={e => setFiltroServico(e.target.value)} value={filtroServico}>
                    <option value="">Todos Serviços</option>
                    {todosServicos.map(s => <option key={s} value={s}>{s}</option>)}
                </select>
             </div>
          </div>

          <button onClick={abrirModalNovo} className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 rounded-lg flex items-center justify-center gap-2 font-medium text-sm transition shadow-sm mt-2">
            <Plus size={16} /> Novo Parceiro
          </button>
        </div>
        
        <div className="overflow-y-auto flex-1 p-2 space-y-2 scrollbar-thin bg-gray-50">
          {parceirosFiltrados.map((p) => (
              <div key={p.id} onClick={() => setParceiroSelecionado(p)}
                className={`p-3 rounded-xl cursor-pointer border transition-all hover:shadow-md ${
                  parceiroSelecionado?.id === p.id ? 'bg-blue-50 border-blue-500 ring-1 ring-blue-500' : 'bg-white border-gray-200'
                }`}
              >
                <div className="flex justify-between items-start">
                  <span className="font-bold text-gray-800 text-sm">{p.empresa}</span>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase ${
                    p.status === 'Diamante' ? 'bg-cyan-100 text-cyan-700' :
                    p.status === 'Ouro' ? 'bg-yellow-100 text-yellow-700' :
                    p.status === 'Prata' ? 'bg-gray-200 text-gray-600' : 'bg-orange-100 text-orange-700'
                  }`}>{p.status}</span>
                </div>
                <div className="flex items-center gap-1 mt-1 flex-wrap">
                    {p.estados_lista && p.estados_lista.slice(0, 4).map(uf => (
                        <span key={uf} className="text-[10px] bg-gray-100 text-gray-600 px-1 rounded border border-gray-200">{uf}</span>
                    ))}
                </div>
              </div>
            )
          )}
        </div>
      </div>

      {/* COLUNA DIREITA */}
      <div className="w-2/3 overflow-y-auto bg-gray-50 p-6 md:p-8">
        {parceiroSelecionado ? (
          <div className="max-w-4xl mx-auto space-y-6 pb-20">
            
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 relative overflow-hidden">
              <div className="flex justify-between items-start relative z-10">
                <div className='flex-1'>
                  <div className="flex items-center gap-3">
                     <h1 className="text-3xl font-bold text-gray-800">{parceiroSelecionado.empresa}</h1>
                     {/* BOTÃO DE EDITAR (NOVO) */}
                     <button onClick={abrirModalEdicao} className="text-gray-400 hover:text-blue-600 transition-colors p-1 rounded-full hover:bg-blue-50" title="Editar Parceiro">
                        <Edit2 size={18}/>
                     </button>
                  </div>
                  
                  <div className="flex flex-wrap gap-2 mt-2">
                     {parceiroSelecionado.estados_lista && parceiroSelecionado.estados_lista.map(uf => (
                        <span key={uf} className="flex items-center gap-1 text-xs font-bold bg-blue-50 text-blue-700 px-2 py-1 rounded-md border border-blue-100">
                            <MapPin size={10}/> {uf}
                        </span>
                     ))}
                  </div>

                  <div className="flex items-center gap-4 mt-4 text-sm text-gray-500">
                    <span className="flex items-center gap-1 bg-gray-100 px-2 py-1 rounded"><User size={14}/> {parceiroSelecionado.contato_nome}</span>
                    <span className="flex items-center gap-1"><Calendar size={14}/> Última: <strong>{parceiroSelecionado.ultima_indicacao || "Nunca"}</strong></span>
                  </div>
                </div>
                
                <div className="flex flex-col items-end gap-3">
                  <div className="text-right">
                    <p className="text-xs text-gray-400 uppercase font-bold tracking-widest">Score</p>
                    <p className="text-5xl font-extrabold text-blue-600 tracking-tighter">{parceiroSelecionado.score_atual}</p>
                  </div>
                  <div className="flex gap-2">
                      <button onClick={() => registrarMovimentacao('Indicação')} className="bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold py-2 px-3 rounded-lg shadow-sm transition-all active:scale-95">
                        + Indicação
                      </button>
                      <button onClick={() => registrarMovimentacao('Venda')} className="bg-green-600 hover:bg-green-700 text-white text-xs font-bold py-2 px-3 rounded-lg shadow-sm transition-all active:scale-95">
                        $$ Venda
                      </button>
                  </div>
                </div>
              </div>
            </div>

            {/* Mantive o restante igual (Gráfico, Histórico, etc) */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                <h3 className="font-bold text-gray-700 flex items-center gap-2 mb-4"><TrendingUp size={18} className="text-green-500"/> Progresso</h3>
                <div className="flex justify-between text-xs font-bold text-gray-500 uppercase mb-2">
                  <span>{parceiroSelecionado.status}</span>
                  <span className="text-blue-600">{getProgresso(parceiroSelecionado.score_atual).label}</span>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-3">
                  <div className="bg-gradient-to-r from-blue-500 to-cyan-400 h-3 rounded-full transition-all duration-500" style={{ width: `${getProgresso(parceiroSelecionado.score_atual).pct}%` }}></div>
                </div>
              </div>
              <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex items-center justify-between">
                 <div>
                    <h3 className="font-bold text-gray-700 flex items-center gap-2 mb-1"><Clock size={18} className="text-orange-500"/> Inatividade</h3>
                    <p className="text-sm text-gray-500">Dias sem indicar: <strong className="text-gray-800">{parceiroSelecionado.dias_sem_indicar}</strong></p>
                 </div>
                 <div className="text-right">
                    <p className="text-xs text-gray-400">Penalidade Estimada</p>
                    <p className="text-xl font-bold text-red-500">-{parceiroSelecionado.multa_estimada} pts</p>
                 </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                <h3 className="font-bold text-gray-700 mb-4 flex items-center gap-2"><History size={18} className="text-purple-500"/> Histórico de Pontuação</h3>
                <div className="overflow-hidden rounded-lg border border-gray-100">
                    <table className="w-full text-sm text-left text-gray-500">
                        <thead className="text-xs text-gray-700 uppercase bg-gray-50">
                            <tr><th className="px-4 py-3">Data</th><th className="px-4 py-3">Tipo</th><th className="px-4 py-3 text-right">Pontos</th></tr>
                        </thead>
                        <tbody>
                            {parceiroSelecionado.historico && parceiroSelecionado.historico.length > 0 ? (
                                parceiroSelecionado.historico.map((item) => (
                                    <tr key={item.id} className="bg-white border-b hover:bg-gray-50">
                                        <td className="px-4 py-3 font-medium text-gray-900">{item.data_formatada}</td>
                                        <td className="px-4 py-3"><span className={`px-2 py-1 rounded text-xs font-bold ${item.tipo === 'Venda' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'}`}>{item.tipo}</span></td>
                                        <td className="px-4 py-3 text-right font-bold text-gray-800">+{item.pontos}</td>
                                    </tr>
                                ))
                            ) : (<tr><td colSpan="3" className="px-4 py-6 text-center text-gray-400 italic">Nenhum histórico encontrado.</td></tr>)}
                        </tbody>
                    </table>
                </div>
            </div>

            <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
              <h3 className="font-bold text-gray-700 mb-4 flex items-center gap-2"><CheckCircle size={18} className="text-gray-400"/> Serviços Habilitados</h3>
              <div className="flex flex-wrap gap-2">
                {parceiroSelecionado.servicos_lista && parceiroSelecionado.servicos_lista.length > 0 ? (
                    parceiroSelecionado.servicos_lista.map((servico) => (<div key={servico} className="px-3 py-2 rounded-lg text-xs font-semibold border bg-gray-50 text-gray-600 border-gray-200">{servico}</div>))
                ) : <p className="text-sm text-gray-400 italic">Nenhum serviço cadastrado.</p>}
              </div>
            </div>

          </div>
        ) : (
          <div className="h-full flex flex-col items-center justify-center text-gray-400 opacity-50"><Briefcase size={48} className="mb-2"/><p>Selecione um parceiro ao lado para ver os detalhes</p></div>
        )}
      </div>
    </div>
  );
};

export default AbaParceiros;
