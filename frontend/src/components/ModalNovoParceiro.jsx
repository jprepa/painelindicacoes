import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { X, Save, Check } from 'lucide-react';

const ESTADOS_BRASIL = [
  'SP', 'RJ', 'MG', 'ES', 'PR', 'SC', 'RS', 
  'MS', 'MT', 'GO', 'DF', 'BA', 'PE', 'CE', 'AM'
]; // Adicione outros se precisar

const ModalNovoParceiro = ({ aoFechar, aoSalvar, parceiroParaEditar = null }) => {
  const [loading, setLoading] = useState(false);
  
  // Estado do formulário
  const [form, setForm] = useState({
    empresa: '',
    contato_nome: '',
    cidade: '',
    servicos: '',
    estados_atuacao: '' // String separada por vírgula
  });

  // Se for EDICÃO, preenche os dados
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

  // Lógica visual para os Estados (Toggle)
  const toggleEstado = (uf) => {
    const listaAtual = form.estados_atuacao 
      ? form.estados_atuacao.split(',').map(s => s.trim()).filter(Boolean) 
      : [];
    
    let novaLista;
    if (listaAtual.includes(uf)) {
      novaLista = listaAtual.filter(item => item !== uf); // Remove
    } else {
      novaLista = [...listaAtual, uf]; // Adiciona
    }
    
    setForm({ ...form, estados_atuacao: novaLista.join(', ') });
  };

  const salvar = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      let response;
      if (parceiroParaEditar) {
        // EDICÃO (PATCH)
        response = await axios.patch(
          `https://prevision-backend.onrender.com/api/parceiros/${parceiroParaEditar.id}/`,
          form
        );
        alert("Parceiro atualizado com sucesso!");
      } else {
        // CRIAÇÃO (POST)
        response = await axios.post(
          'https://prevision-backend.onrender.com/api/parceiros/',
          form
        );
        alert("Parceiro cadastrado com sucesso!");
      }

      aoSalvar(response.data); // Manda o dado novo/atualizado de volta pra tela
      aoFechar();
    } catch (error) {
      console.error("Erro:", error);
      alert("Erro ao salvar. Verifique os campos.");
    } finally {
      setLoading(false);
    }
  };

  // Helper para saber se o estado está marcado
  const isMarcado = (uf) => {
    if (!form.estados_atuacao) return false;
    return form.estados_atuacao.split(',').map(s => s.trim()).includes(uf);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden flex flex-col max-h-[90vh]">
        
        {/* Cabeçalho */}
        <div className="px-6 py-4 border-b border-gray-100 flex justify-between items-center bg-gray-50">
          <h2 className="text-lg font-bold text-gray-800">
            {parceiroParaEditar ? `Editar ${parceiroParaEditar.empresa}` : 'Novo Parceiro'}
          </h2>
          <button onClick={aoFechar} className="p-2 hover:bg-gray-200 rounded-full text-gray-500">
            <X size={20} />
          </button>
        </div>

        {/* Formulário com Scroll */}
        <div className="p-6 space-y-4 overflow-y-auto">
          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Nome da Empresa</label>
            <input 
              name="empresa" value={form.empresa} onChange={handleChange}
              className="w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" 
              placeholder="Ex: Construtora XYZ"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Contato</label>
              <input 
                name="contato_nome" value={form.contato_nome} onChange={handleChange}
                className="w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" 
                placeholder="Nome do responsável"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Cidade Base</label>
              <input 
                name="cidade" value={form.cidade} onChange={handleChange}
                className="w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" 
                placeholder="Ex: São Paulo"
              />
            </div>
          </div>

          {/* SELETOR DE ESTADOS (ÁREA DE ATUAÇÃO) */}
          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-2">Área de Atuação (Estados)</label>
            <div className="flex flex-wrap gap-2 p-3 bg-gray-50 rounded-xl border border-gray-100">
              {ESTADOS_BRASIL.map(uf => (
                <button
                  key={uf}
                  type="button"
                  onClick={() => toggleEstado(uf)}
                  className={`text-xs font-bold px-3 py-1.5 rounded-lg border transition-all ${
                    isMarcado(uf) 
                      ? 'bg-blue-600 text-white border-blue-600 shadow-md transform scale-105' 
                      : 'bg-white text-gray-500 border-gray-200 hover:border-blue-300'
                  }`}
                >
                  {uf}
                </button>
              ))}
            </div>
            <p className="text-[10px] text-gray-400 mt-1 text-right">Selecione onde o parceiro atua para filtrar depois.</p>
          </div>

          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-1">Serviços (Separados por vírgula)</label>
            <textarea 
              name="servicos" value={form.servicos} onChange={handleChange} rows={2}
              className="w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none resize-none"
              placeholder="Ex: Projetos, Obras, Consultoria..."
            />
          </div>
        </div>

        {/* Rodapé */}
        <div className="p-4 border-t border-gray-100 bg-gray-50 flex justify-end gap-2">
          <button onClick={aoFechar} className="px-4 py-2 text-sm font-bold text-gray-600 hover:bg-gray-200 rounded-lg">
            Cancelar
          </button>
          <button 
            onClick={salvar} 
            disabled={loading}
            className="px-6 py-2 text-sm font-bold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-lg flex items-center gap-2 disabled:opacity-50"
          >
            {loading ? 'Salvando...' : <><Save size={16}/> Salvar Parceiro</>}
          </button>
        </div>

      </div>
    </div>
  );
};

export default ModalNovoParceiro;
