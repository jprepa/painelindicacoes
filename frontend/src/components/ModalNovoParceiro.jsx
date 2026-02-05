import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { X, Save, Check, Briefcase } from 'lucide-react';

const ESTADOS_BRASIL = [
  'SP', 'RJ', 'MG', 'ES', 'PR', 'SC', 'RS', 
  'MS', 'MT', 'GO', 'DF', 'BA', 'PE', 'CE', 'AM'
];

// Lista baseada nos seus prints
const LISTA_SERVICOS = [
  "Estudo de Viabilidade",
  "Gerenciamento Obra",
  "Gestão de Pessoas",
  "Ger. Físico-Financeiro",
  "Soluções Sustentáveis",
  "Projetos Complementares",
  "Consultoria",
  "Cursos",
  "BIM",
  "Qualidade",
  "Monitoramento e Controle"
];

const ModalNovoParceiro = ({ aoFechar, aoSalvar, parceiroParaEditar = null }) => {
  const [loading, setLoading] = useState(false);
  
  const [form, setForm] = useState({
    empresa: '',
    contato_nome: '',
    cidade: '',
    servicos: '', // Continua sendo string pro backend (ex: "BIM, Cursos")
    estados_atuacao: '' 
  });

  // Preenche se for edição
  useEffect(() => {
    if (parceiroParaEditar) {
      setForm({
        empresa: parceiroParaEditar.empresa || '',
        contato_nome: parceiroParaEditar.contato_nome || '',
        cidade: parceiroParaEditar.cidade || '',
        servicos: parceiroParaEditar.servicos || '',
        estados_atuacao: parceiroParaEditar.estados_atuacao || ''
      });
    }
  }, [parceiroParaEditar]);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  // --- LÓGICA ESTADOS (Já existia) ---
  const toggleEstado = (uf) => {
    const lista = form.estados_atuacao ? form.estados_atuacao.split(',').map(s => s.trim()).filter(Boolean) : [];
    const novaLista = lista.includes(uf) ? lista.filter(i => i !== uf) : [...lista, uf];
    setForm({ ...form, estados_atuacao: novaLista.join(', ') });
  };

  // --- LÓGICA SERVIÇOS (Nova) ---
  const toggleServico = (servico) => {
    // Transforma a string do banco em array
    const lista = form.servicos ? form.servicos.split(',').map(s => s.trim()).filter(Boolean) : [];
    
    // Adiciona ou Remove
    const novaLista = lista.includes(servico) 
      ? lista.filter(i => i !== servico) 
      : [...lista, servico];
    
    // Transforma de volta em string pro banco
    setForm({ ...form, servicos: novaLista.join(', ') });
  };

  // Helpers visuais
  const isEstadoMarcado = (uf) => form.estados_atuacao?.includes(uf);
  const isServicoMarcado = (srv) => {
    if (!form.servicos) return false;
    // Verifica exato para não confundir nomes parecidos
    const lista = form.servicos.split(',').map(s => s.trim());
    return lista.includes(srv);
  };

  const salvar = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      let response;
      if (parceiroParaEditar) {
        response = await axios.patch(`https://prevision-backend.onrender.com/api/parceiros/${parceiroParaEditar.id}/`, form);
        alert("Atualizado com sucesso!");
      } else {
        response = await axios.post('https://prevision-backend.onrender.com/api/parceiros/', form);
        alert("Criado com sucesso!");
      }
      aoSalvar(response.data);
      aoFechar();
    } catch (error) {
      console.error(error);
      alert("Erro ao salvar.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 backdrop-blur-sm p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden flex flex-col max-h-[90vh]">
        
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-100 flex justify-between items-center bg-gray-50">
          <h2 className="text-lg font-bold text-gray-800 flex items-center gap-2">
            {parceiroParaEditar ? <Briefcase size={20}/> : <Briefcase size={20}/>}
            {parceiroParaEditar ? `Editar ${parceiroParaEditar.empresa}` : 'Novo Parceiro'}
          </h2>
          <button onClick={aoFechar} className="p-2 hover:bg-gray-200 rounded-full text-gray-500"><X size={20} /></button>
        </div>

        {/* Scrollable Content */}
        <div className="p-6 space-y-5 overflow-y-auto scrollbar-thin">
          
          {/* Dados Básicos */}
          <div className="space-y-3">
            <div>
              <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Nome da Empresa</label>
              <input name="empresa" value={form.empresa} onChange={handleChange}
                className="w-full p-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none text-sm" 
                placeholder="Ex: Construtora XYZ" />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Contato</label>
                <input name="contato_nome" value={form.contato_nome} onChange={handleChange}
                  className="w-full p-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none text-sm" 
                  placeholder="Nome do responsável" />
              </div>
              <div>
                <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Cidade Base</label>
                <input name="cidade" value={form.cidade} onChange={handleChange}
                  className="w-full p-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none text-sm" 
                  placeholder="Ex: São Paulo" />
              </div>
            </div>
          </div>

          <hr className="border-gray-100"/>

          {/* ÁREA DE ATUAÇÃO (ESTADOS) */}
          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-2 flex justify-between">
              Área de Atuação
              <span className="text-[10px] text-gray-400 font-normal">Onde a empresa atua?</span>
            </label>
            <div className="flex flex-wrap gap-2">
              {ESTADOS_BRASIL.map(uf => (
                <button
                  key={uf} type="button" onClick={() => toggleEstado(uf)}
                  className={`text-xs font-bold px-3 py-1.5 rounded-lg border transition-all ${
                    isEstadoMarcado(uf) 
                      ? 'bg-blue-600 text-white border-blue-600 shadow-sm' 
                      : 'bg-white text-gray-500 border-gray-200 hover:border-blue-300'
                  }`}
                >
                  {uf}
                </button>
              ))}
            </div>
          </div>

          <hr className="border-gray-100"/>

          {/* SERVIÇOS (AGORA COM BOTÕES) */}
          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-2 flex justify-between">
              Serviços Prestados
              <span className="text-[10px] text-gray-400 font-normal">Selecione os serviços</span>
            </label>
            <div className="flex flex-wrap gap-2">
              {LISTA_SERVICOS.map(srv => (
                <button
                  key={srv} type="button" onClick={() => toggleServico(srv)}
                  className={`text-xs font-bold px-3 py-2 rounded-lg border transition-all flex items-center gap-1 ${
                    isServicoMarcado(srv) 
                      ? 'bg-green-600 text-white border-green-600 shadow-sm' 
                      : 'bg-white text-gray-600 border-gray-200 hover:border-green-300'
                  }`}
                >
                  {isServicoMarcado(srv) && <Check size={12} strokeWidth={4}/>}
                  {srv}
                </button>
              ))}
            </div>
            {/* Campo extra caso queira digitar algo fora da lista */}
            <input 
               className="mt-3 w-full text-xs p-2 border border-gray-200 rounded text-gray-500 placeholder-gray-300 focus:outline-none focus:border-gray-400"
               placeholder="Outros serviços (digite manual se precisar)..."
               value={form.servicos} 
               onChange={handleChange}
               name="servicos"
            />
          </div>

        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-100 bg-gray-50 flex justify-end gap-3">
          <button onClick={aoFechar} className="px-4 py-2 text-sm font-bold text-gray-600 hover:bg-gray-200 rounded-lg transition-colors">
            Cancelar
          </button>
          <button onClick={salvar} disabled={loading}
            className="px-6 py-2 text-sm font-bold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-md flex items-center gap-2 transition-transform active:scale-95 disabled:opacity-50">
            {loading ? 'Salvando...' : <><Save size={16}/> Salvar Parceiro</>}
          </button>
        </div>

      </div>
    </div>
  );
};

export default ModalNovoParceiro;
