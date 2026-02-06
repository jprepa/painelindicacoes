import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { MapPin, Briefcase, TrendingUp, Calendar, User, Clock, Plus, History, CheckCircle, Edit2, UploadCloud, Loader2, Mail, Phone, ChevronDown, Check } from 'lucide-react';
import ModalNovoParceiro from './ModalNovoParceiro';

// --- COMPONENTE DE MULTI-SELEÇÃO (DROPDOWN) ---
const MultiSelect = ({ label, options, selected, onChange }) => {
  const [isOpen, setIsOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (ref.current && !ref.current.contains(event.target)) setIsOpen(false);
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const toggleOption = (option) => {
    if (selected.includes(option)) {
      onChange(selected.filter(item => item !== option));
    } else {
      onChange([...selected, option]);
    }
  };

  return (
    <div className="relative w-1/2" ref={ref}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`w-full text-xs p-2 border rounded-lg bg-white text-left flex justify-between items-center transition-all ${selected.length > 0 ? 'border-blue-500 text-blue-700 bg-blue-50' : 'text-gray-500 border-gray-200'}`}
      >
        <span className="truncate font-medium">
            {selected.length === 0 ? label : `${selected.length} selecionados`}
        </span>
        <ChevronDown size={14} className={`transition-transform ${isOpen ? 'rotate-180' : ''}`}/>
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-xl z-50 max-h-60 overflow-y-auto scrollbar-thin">
          {options.length > 0 ? options.map(opt => (
            <div
              key={opt}
              onClick={() => toggleOption(opt)}
              className="px-3 py-2 text-xs flex items-center gap-2 hover:bg-gray-50 cursor-pointer text-gray-700 border-b border-gray-50 last:border-0"
            >
              <div className={`w-3 h-3 border rounded flex items-center justify-center transition-colors ${selected.includes(opt) ? 'bg-blue-600 border-blue-600' : 'border-gray-300 bg-white'}`}>
                {selected.includes(opt) && <Check size={8} className="text-white" strokeWidth={4}/>}
              </div>
              <span className={selected.includes(opt) ? 'font-bold text-gray-900' : ''}>{opt}</span>
            </div>
          )) : <div className="p-2 text-center text-xs text-gray-400">Nenhuma opção</div>}
        </div>
      )}
    </div>
  );
};

const AbaParceiros = () => {
  const [parceiroSelecionado, setParceiroSelecionado] = useState(null);
  const [parceiros, setParceiros] = useState([]);
  const [loading, setLoading] = useState(true);
  
  const fileInputRef = useRef(null);
  const [uploading, setUploading] = useState(false);
  const [mostrarModal, setMostrarModal] = useState(false);
  const [parceiroParaEditar, setParceiroParaEditar] = useState(null);

  // Filtros
  const [filtroTexto, setFiltroTexto] = useState("");
  const [filtrosEstados, setFiltrosEstados] = useState([]); 
  const [filtrosServicos, setFiltrosServicos] = useState([]); 

  useEffect(() => { carregarParceiros(); }, []);

  const carregarParceiros = () => {
    setLoading(true);
    axios.get('https://prevision-backend.onrender.com/api/parceiros/')
      .then(response => { setParceiros(response.data); setLoading(false); })
      .catch(erro => console.error(erro));
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    try {
      const response = await axios.post('https://prevision-backend.onrender.com/api/parceiros/importar_excel/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      alert(response.data.mensagem);
      carregarParceiros();
    } catch (error) { alert("Erro ao importar."); } 
    finally { setUploading(false); if(fileInputRef.current) fileInputRef.current.value = ""; }
  };

  const aoSalvarParceiro = (parceiroAtualizado) => {
    const existe = parceiros.find(p => p.id === parceiroAtualizado.id);
    if (existe) {
      setParceiros(parceiros.map(p => p.id === parceiroAtualizado.id ? parceiroAtualizado : p));
      if (parceiroSelecionado?.id === parceiroAtualizado.id) setParceiroSelecionado(parceiroAtualizado);
    } else {
      setParceiros([parceiroAtualizado, ...parceiros]);
      setParceiroSelecionado(parceiroAtualizado);
    }
    setMostrarModal(false); setParceiroParaEditar(null);
  };

  const registrarMovimentacao = async (tipo) => {
    if (!parceiroSelecionado) return;
    const valorPadrao = tipo === 'Venda' ? "1.0" : "0.7";
    const pontos = prompt(`Pontos para ${tipo}?`, valorPadrao);
    if (pontos) {
      try {
        const response = await axios.post(`https://prevision-backend.onrender.com/api/parceiros/${parceiroSelecionado.id}/registrar_indicacao/`, { pontos, tipo });
        const atualizado = response.data;
        setParceiros(parceiros.map(p => p.id === atualizado.id ? atualizado : p));
        setParceiroSelecionado(atualizado);
        alert("Salvo!");
      } catch (error) { alert("Erro ao salvar."); }
    }
  };

  const todosEstados = [...new Set(parceiros.flatMap(p => p.estados_lista || []))].sort();
  const todosServicos = [...new Set(parceiros.flatMap(p => p.servicos_lista || []))].sort();

  const parceirosFiltrados = parceiros.filter(p => {
    const matchTexto = p.empresa.toLowerCase().includes(filtroTexto.toLowerCase());
    const matchEstado = filtrosEstados.length === 0 ? true : p.estados_lista && p.estados_lista.some(uf => filtrosEstados.includes(uf));
    const matchServico = filtrosServicos.length === 0 ? true : p.servicos_lista && p.servicos_lista.some(srv => filtrosServicos.includes(srv));
    return matchTexto && matchEstado && matchServico;
  });

  const getProgresso = (score) => {
    const s = parseFloat(score || 0);
    const niveis = { bronze: 1.7, prata: 2.4, ouro: 3.4, diamante: 6.1 };
    if (s < niveis.bronze) return { pct: (s/1.7)*100, label: `Faltam ${(1.7-s).toFixed(1)} para Bronze` };
    if (s < niveis.prata) return { pct: ((s-1.7)/(2.4-1.7))*100, label: `Faltam ${(2.4-s).toFixed(1)} para Prata` };
    if (s < niveis.ouro) return { pct: ((s-2.4)/(3.4-2.4))*100, label: `Faltam ${(3.4-s).toFixed(1)} para Ouro` };
    if (s < niveis.diamante) return { pct: ((s-3.4)/(6.1-3.4))*100, label: `Faltam ${(6.1-s).toFixed(1)} para Diamante` };
    return { pct: 100, label: "Topo Alcançado!" };
  };

  return (
    <div className="flex h-full bg-gray-50 overflow-hidden relative">
      {mostrarModal && <ModalNovoParceiro aoFechar={() => setMostrarModal(false)} aoSalvar={aoSalvarParceiro} parceiroParaEditar={parceiroParaEditar} />}
      <input type="file" ref={fileInputRef} onChange={handleFileUpload} className="hidden" accept=".xlsx, .xls" />

      {/* LISTA */}
      <div className="w-1/3 bg-white border-r border-gray-200 flex flex-col shadow-lg z-10">
        <div className="p-4 border-b border-gray-100 bg-white space-y-3">
          <h2 className="text-lg font-bold text-gray-800 flex items-center gap-2"><Briefcase size={20} className="text-blue-600"/> Parceiros ({parceirosFiltrados.length})</h2>
          <div className="space-y-2">
             <input type="text" placeholder="Buscar..." className="w-full text-sm p-2 border rounded-lg bg-gray-50" value={filtroTexto} onChange={e => setFiltroTexto(e.target.value)} />
             <div className="flex gap-2">
                <MultiSelect label="Estados" options={todosEstados} selected={filtrosEstados} onChange={setFiltrosEstados} />
                <MultiSelect label="Serviços" options={todosServicos} selected={filtrosServicos} onChange={setFiltrosServicos} />
             </div>
          </div>
          <div className="flex gap-2 mt-2">
            <button onClick={() => fileInputRef.current.click()} disabled={uploading} className="w-1/3 bg-green-600 hover:bg-green-700 text-white py-2 rounded-lg flex items-center justify-center gap-2 font-medium text-xs disabled:opacity-50">{uploading ? <Loader2 size={16} className="animate-spin"/> : <UploadCloud size={16} />} Importar</button>
            <button onClick={() => { setParceiroParaEditar(null); setMostrarModal(true); }} className="w-2/3 bg-blue-600 hover:bg-blue-700 text-white py-2 rounded-lg flex items-center justify-center gap-2 font-medium text-sm"><Plus size={16} /> Novo Parceiro</button>
          </div>
        </div>
        
        {/* LISTA DE PARCEIROS */}
        <div className="overflow-y-auto flex-1 p-2 space-y-2 scrollbar-thin bg-gray-50">
          {loading ? <p className="text-center text-gray-400 mt-10">Carregando...</p> : parceirosFiltrados.map((p) => (
              <div key={p.id} onClick={() => setParceiroSelecionado(p)} className={`p-3 rounded-xl cursor-pointer border transition-all hover:shadow-md ${parceiroSelecionado?.id === p.id ? 'bg-blue-50 border-blue-500 ring-1 ring-blue-500' : 'bg-white border-gray-200'}`}>
                <div className="flex justify-between items-start">
                  <span className="font-bold text-gray-800 text-sm truncate">{p.empresa}</span>
                  
                  {/* SÓ MOSTRA O SELO SE NÃO FOR 'EM ANÁLISE' */}
                  {p.status !== 'Em análise' && (
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase ${
                        p.status === 'Diamante' ? 'bg-cyan-100 text-cyan-700' : 
                        p.status === 'Ouro' ? 'bg-yellow-100 text-yellow-700' : 
                        p.status === 'Prata' ? 'bg-gray-200 text-gray-600' : 
                        'bg-orange-100 text-orange-700' // Bronze
                    }`}>
                        {p.status}
                    </span>
                  )}

                </div>
                <div className="flex items-center gap-1 mt-1 flex-wrap">{p.estados_lista && p.estados_lista.slice(0, 4).map(uf => (<span key={uf} className="text-[10px] bg-gray-100 text-gray-600 px-1 rounded border border-gray-200">{uf}</span>))}</div>
              </div>
          ))}
        </div>
      </div>

      {/* DETALHES */}
      <div className="w-2/3 overflow-y-auto bg-gray-50 p-6 md:p-8">
        {parceiroSelecionado ? (
          <div className="max-w-4xl mx-auto space-y-6 pb-20">
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 relative overflow-hidden">
              <div className="flex justify-between items-start relative z-10">
                <div className='flex-1'>
                  <div className="flex items-center gap-3">
                     <h1 className="text-3xl font-bold text-gray-800">{parceiroSelecionado.empresa}</h1>
                     <button onClick={() => { setParceiroParaEditar(parceiroSelecionado); setMostrarModal(true); }} className="text-gray-400 hover:text-blue-600 transition-colors p-1 rounded-full hover:bg-blue-50"><Edit2 size={18}/></button>
                  </div>
                  
                  <div className="flex flex-wrap gap-2 mt-2 mb-4">
                     {parceiroSelecionado.cidade && <span className="flex items-center gap-1 text-xs font-bold bg-gray-100 text-gray-600 px-2 py-1 rounded-md border border-gray-200"><MapPin size={10}/> {parceiroSelecionado.cidade}</span>}
                     {parceiroSelecionado.estados_lista && parceiroSelecionado.estados_lista.map(uf => (<span key={uf} className="flex items-center gap-1 text-xs font-bold bg-blue-50 text-blue-700 px-2 py-1 rounded-md border border-blue-100">{uf}</span>))}
                  </div>

                  <div className="flex flex-col gap-1 text-sm text-gray-600 bg-gray-50 p-3 rounded-lg border border-gray-100 w-fit">
                    <span className="flex items-center gap-2 font-bold text-gray-800"><User size={14}/> {parceiroSelecionado.contato_nome || "Sem contato"}</span>
                    {parceiroSelecionado.email && <span className="flex items-center gap-2"><Mail size={14} className="text-gray-400"/> {parceiroSelecionado.email}</span>}
                    {parceiroSelecionado.telefone && <span className="flex items-center gap-2"><Phone size={14} className="text-gray-400"/> {parceiroSelecionado.telefone}</span>}
                  </div>
                </div>
                <div className="flex flex-col items-end gap-3">
                  <div className="text-right">
                    <p className="text-xs text-gray-400 uppercase font-bold tracking-widest">Score (90 Dias)</p>
                    <p className="text-5xl font-extrabold text-blue-600 tracking-tighter">{parceiroSelecionado.score_atual}</p>
                  </div>
                  <div className="flex gap-2">
                      <button onClick={() => registrarMovimentacao('Indicação')} className="bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold py-2 px-3 rounded-lg shadow-sm active:scale-95">+ Indicação</button>
                      <button onClick={() => registrarMovimentacao('Venda')} className="bg-green-600 hover:bg-green-700 text-white text-xs font-bold py-2 px-3 rounded-lg shadow-sm active:scale-95">$$ Venda</button>
                  </div>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                <h3 className="font-bold text-gray-700 flex items-center gap-2 mb-4"><TrendingUp size={18} className="text-green-500"/> Progresso</h3>
                <div className="flex justify-between text-xs font-bold text-gray-500 uppercase mb-2">
                  <span>{parceiroSelecionado.status}</span><span className="text-blue-600">{getProgresso(parceiroSelecionado.score_atual).label}</span>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-3">
                  <div className="bg-gradient-to-r from-blue-500 to-cyan-400 h-3 rounded-full transition-all duration-500" style={{ width: `${getProgresso(parceiroSelecionado.score_atual).pct}%` }}></div>
                </div>
              </div>

              <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex flex-col justify-center">
                 <h3 className="font-bold text-gray-700 flex items-center gap-2 mb-2"><Clock size={18} className="text-orange-500"/> Próximo Vencimento</h3>
                 {parceiroSelecionado.vencimento_info ? (
                   <div className="flex justify-between items-center mt-2">
                     <div>
                        <p className="text-3xl font-extrabold text-gray-800">{parceiroSelecionado.vencimento_info.dias} <span className="text-sm font-medium text-gray-400">dias restantes</span></p>
                        <p className="text-xs text-orange-600 font-bold mt-1">Pontos vão expirar em breve</p>
                     </div>
                     <div className="text-right bg-red-50 px-3 py-2 rounded-lg border border-red-100">
                        <p className="text-xs text-red-400 font-bold uppercase">A perder</p>
                        <p className="text-xl font-bold text-red-600">-{parceiroSelecionado.vencimento_info.pontos} pts</p>
                     </div>
                   </div>
                 ) : (
                   <div className="flex items-center gap-2 text-gray-400 mt-2">
                      <CheckCircle size={20} className="text-green-500"/>
                      <p className="text-sm">Nenhum ponto prestes a vencer.</p>
                   </div>
                 )}
              </div>
            </div>

            <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                <h3 className="font-bold text-gray-700 mb-4 flex items-center gap-2"><History size={18} className="text-purple-500"/> Histórico de Pontuação</h3>
                <div className="overflow-hidden rounded-lg border border-gray-100">
                    <table className="w-full text-sm text-left text-gray-500">
                        <thead className="text-xs text-gray-700 uppercase bg-gray-50"><tr><th className="px-4 py-3">Data</th><th className="px-4 py-3">Tipo</th><th className="px-4 py-3 text-right">Pontos</th></tr></thead>
                        <tbody>
                            {parceiroSelecionado.historico && parceiroSelecionado.historico.length > 0 ? (
                                parceiroSelecionado.historico.map((item) => (<tr key={item.id} className="bg-white border-b hover:bg-gray-50"><td className="px-4 py-3">{item.data_formatada}</td><td className="px-4 py-3"><span className={`px-2 py-1 rounded text-xs font-bold ${item.tipo === 'Venda' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'}`}>{item.tipo}</span></td><td className="px-4 py-3 text-right font-bold text-gray-800">+{item.pontos}</td></tr>))
                            ) : (<tr><td colSpan="3" className="px-4 py-6 text-center text-gray-400 italic">Nenhum histórico encontrado.</td></tr>)}
                        </tbody>
                    </table>
                </div>
            </div>

            <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
              <h3 className="font-bold text-gray-700 mb-4 flex items-center gap-2"><CheckCircle size={18} className="text-gray-400"/> Serviços Habilitados</h3>
              <div className="flex flex-wrap gap-2">
                {parceiroSelecionado.servicos_lista && parceiroSelecionado.servicos_lista.length > 0 ? (parceiroSelecionado.servicos_lista.map((servico) => (<div key={servico} className="px-3 py-2 rounded-lg text-xs font-semibold border bg-gray-50 text-gray-600 border-gray-200">{servico}</div>))) : <p className="text-sm text-gray-400 italic">Nenhum serviço cadastrado.</p>}
              </div>
            </div>
          </div>
        ) : <div className="h-full flex flex-col items-center justify-center text-gray-400 opacity-50"><Briefcase size={48} className="mb-2"/><p>Selecione um parceiro</p></div>}
      </div>
    </div>
  );
};

export default AbaParceiros;
