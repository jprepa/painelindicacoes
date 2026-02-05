import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { X, Save, Check, Briefcase } from 'lucide-react';

const ESTADOS_BRASIL = [
  'SP', 'RJ', 'MG', 'ES', 'PR', 'SC', 'RS', 
  'MS', 'MT', 'GO', 'DF', 'BA', 'PE', 'CE', 'AM', 'PA', 'MA'
];

// LISTA ATUALIZADA CONFORME SUA PLANILHA
const LISTA_SERVICOS = [
  "Planejamento de Projetos/Incorporação",
  "Estudo de Viabilidade",
  "Orçamento",
  "Planejamento",
  "Monitoramento e Controle",
  "Gerenciamento de Obra",
  "Consultoria",
  "Cursos",
  "BIM",
  "Mentoria Lean",
  "Gestão de Pessoas",
  "Projetos Complementares",
  "Qualidade",
  "Gerenciamento de Projeto/Contrato",
  "Gerenciamento Físico-Financeiro",
  "Soluções Sustentáveis"
];

const ModalNovoParceiro = ({ aoFechar, aoSalvar, parceiroParaEditar = null }) => {
  const [loading, setLoading] = useState(false);
  
  const [form, setForm] = useState({
    empresa: '',
    contato_nome: '',
    cidade: '',
    servicos: '', 
    estados_atuacao: '' 
  });

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

  const toggleEstado = (uf) => {
    const lista = form.estados_atuacao ? form.estados_atuacao.split(',').map(s => s.trim()).filter(Boolean) : [];
    const novaLista = lista.includes(uf) ? lista.filter(i => i !== uf) : [...lista, uf];
    setForm({ ...form, estados_atuacao: novaLista.join(', ') });
  };

  const toggleServico = (servico) => {
    const lista = form.servicos ? form.servicos.split(',').map(s => s.trim()).filter(Boolean) : [];
    const novaLista = lista.includes(servico) ? lista.filter(i => i !== servico) : [...lista, servico];
    setForm({ ...form, servicos: novaLista.join(', ') });
  };

  const isEstadoMarcado = (uf) => form.estados_atuacao?.includes(uf);
  const isServicoMarcado = (srv) => {
    if (!form.servicos) return false;
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
        <div className="px-6 py-4 border-b border-gray-100 flex justify-between items-center bg-gray-50">
          <h2 className="text-lg font-bold text-gray-800 flex items-center gap-2">
            <Briefcase size={20}/> {parceiroParaEditar ? `Editar ${parceiroParaEditar.empresa}` : 'Novo Parceiro'}
          </h2>
          <button onClick={aoFechar} className="p-2 hover:bg-gray-200 rounded-full text-gray-500"><X size={20} /></button>
        </div>

        <div className="p-6 space-y-5 overflow-y-auto scrollbar-thin">
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
          
          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-2">Área de Atuação</label>
            <div className="flex flex-wrap gap-2">
              {ESTADOS_BRASIL.map(uf => (
                <button key={uf} type="button" onClick={() => toggleEstado(uf)}
                  className={`text-xs font-bold px-3 py-1.5 rounded-lg border transition-all ${isEstadoMarcado(uf) ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-gray-500 border-gray-200'}`}>
                  {uf}
                </button>
              ))}
            </div>
          </div>

          <hr className="border-gray-100"/>

          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-2">Serviços Prestados</label>
            <div className="flex flex-wrap gap-2">
              {LISTA_SERVICOS.map(srv => (
                <button key={srv} type="button" onClick={() => toggleServico(srv)}
                  className={`text-[10px] font-bold px-3 py-2 rounded-lg border transition-all flex items-center gap-1 ${isServicoMarcado(srv) ? 'bg-green-600 text-white border-green-600' : 'bg-white text-gray-600 border-gray-200'}`}>
                  {isServicoMarcado(srv) && <Check size={10} strokeWidth={4}/>} {srv}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="p-4 border-t border-gray-100 bg-gray-50 flex justify-end gap-3">
          <button onClick={aoFechar} className="px-4 py-2 text-sm font-bold text-gray-600 hover:bg-gray-200 rounded-lg">Cancelar</button>
          <button onClick={salvar} disabled={loading} className="px-6 py-2 text-sm font-bold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-md flex items-center gap-2 disabled:opacity-50">
            {loading ? 'Salvando...' : <><Save size={16}/> Salvar Parceiro</>}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ModalNovoParceiro;
