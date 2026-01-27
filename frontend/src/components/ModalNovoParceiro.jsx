import React, { useState } from 'react';
import axios from 'axios';
import { X, Save, Check } from 'lucide-react';

const ModalNovoParceiro = ({ aoFechar, aoSalvar }) => {
  // Estados do formulário
  const [formData, setFormData] = useState({
    empresa: '',
    contato_nome: '',
    email: '',
    telefone: '',
    cidade: '',
    status: 'Bronze',
    score_atual: 0,
    ultima_indicacao: new Date().toISOString().split('T')[0] // Data de hoje
  });

  const [servicosSelecionados, setServicosSelecionados] = useState([]);
  const [salvando, setSalvando] = useState(false);

  // Lista de Serviços para marcar
  const opcoesServicos = [
    "Estudo de Viabilidade", "Orçamento", "Planejamento", "Monitoramento e Controle",
    "Gerenciamento Obra", "Consultoria", "Cursos", "BIM", "Mentoria Lean", 
    "Gestão de Pessoas", "Projetos Complementares", "Qualidade", 
    "Ger. de Projeto/Contrato", "Ger. Físico-Financeiro", "Soluções Sustentáveis"
  ];

  // Atualiza os campos de texto
  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  // Lógica de Marcar/Desmarcar Serviços
  const toggleServico = (servico) => {
    if (servicosSelecionados.includes(servico)) {
      setServicosSelecionados(servicosSelecionados.filter(s => s !== servico));
    } else {
      setServicosSelecionados([...servicosSelecionados, servico]);
    }
  };

  // Enviar para o Django
  const handleSubmit = async (e) => {
    e.preventDefault();
    setSalvando(true);

    // Prepara os dados (converte a lista de serviços para texto virgulado, que o Django espera)
    const dadosParaEnvio = {
      ...formData,
      servicos: servicosSelecionados.join(', ')
    };

    try {
      const response = await axios.post('https://prevision-backend.onrender.com/api/parceiros/', dadosParaEnvio);
      aoSalvar(response.data); // Devolve o novo parceiro para a tela principal
      aoFechar(); // Fecha a janela
    } catch (error) {
      console.error("Erro ao salvar:", error);
      alert("Erro ao salvar parceiro. Verifique os dados.");
    } finally {
      setSalvando(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        
        {/* Cabeçalho */}
        <div className="flex justify-between items-center p-6 border-b sticky top-0 bg-white z-10">
          <h2 className="text-xl font-bold text-gray-800">Novo Parceiro</h2>
          <button onClick={aoFechar} className="text-gray-400 hover:text-red-500 transition">
            <X size={24} />
          </button>
        </div>

        {/* Formulário */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Nome da Empresa *</label>
              <input required name="empresa" value={formData.empresa} onChange={handleChange} className="w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" placeholder="Ex: Construtora X" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Contato (Pessoa) *</label>
              <input required name="contato_nome" value={formData.contato_nome} onChange={handleChange} className="w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" placeholder="Ex: João Silva" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input type="email" name="email" value={formData.email} onChange={handleChange} className="w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Cidade - UF *</label>
              <input required name="cidade" value={formData.cidade} onChange={handleChange} className="w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" placeholder="Ex: Florianópolis - SC" />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Score Inicial</label>
              <input type="number" step="0.1" name="score_atual" value={formData.score_atual} onChange={handleChange} className="w-full p-2 border rounded-lg" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Data Última Indicação</label>
              <input type="date" name="ultima_indicacao" value={formData.ultima_indicacao} onChange={handleChange} className="w-full p-2 border rounded-lg" />
            </div>
          </div>

          {/* Seleção Visual de Serviços */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">Serviços Prestados (Clique para selecionar)</label>
            <div className="flex flex-wrap gap-2">
              {opcoesServicos.map(servico => {
                const ativo = servicosSelecionados.includes(servico);
                return (
                  <button
                    key={servico}
                    type="button"
                    onClick={() => toggleServico(servico)}
                    className={`px-3 py-2 rounded-lg text-xs font-semibold border transition-all flex items-center gap-2 ${
                      ativo 
                        ? 'bg-blue-600 text-white border-blue-600 shadow-md transform scale-105' 
                        : 'bg-gray-50 text-gray-500 border-gray-200 hover:bg-gray-100'
                    }`}
                  >
                    {ativo && <Check size={12} />} {servico}
                  </button>
                )
              })}
            </div>
          </div>

          {/* Rodapé do Form */}
          <div className="pt-4 border-t flex justify-end gap-3">
            <button type="button" onClick={aoFechar} className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg">
              Cancelar
            </button>
            <button 
              type="submit" 
              disabled={salvando}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2 disabled:opacity-50"
            >
              {salvando ? 'Salvando...' : <><Save size={18} /> Cadastrar Parceiro</>}
            </button>
          </div>

        </form>
      </div>
    </div>
  );
};

export default ModalNovoParceiro;