import React, { useState } from 'react';
import axios from 'axios';
import { UploadCloud, FileSpreadsheet, CheckCircle, AlertCircle, Play, Loader2, Database } from 'lucide-react';

const AbaQualificacao = () => {
  const [arquivoLeads, setArquivoLeads] = useState(null);
  const [arquivoClientes, setArquivoClientes] = useState(null); // Novo estado
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("idle");

  const processarLista = async () => {
    if (!arquivoLeads) return;
    setLoading(true);
    setStatus("processing");

    const formData = new FormData();
    formData.append('file', arquivoLeads); // Arquivo principal
    
    // Se tiver arquivo de clientes, anexa também
    if (arquivoClientes) {
      formData.append('file_clientes', arquivoClientes);
    }

    try {
      const response = await axios.post('https://prevision-backend.onrender.com/api/parceiros/qualificar_leads/', formData, {
        responseType: 'blob',
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'Lista_Qualificada_Starian.xlsx');
      document.body.appendChild(link);
      link.click();
      
      setStatus("success");
    } catch (error) {
      console.error(error);
      setStatus("error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-full bg-gray-50 p-8 flex flex-col items-center justify-center overflow-y-auto">
      <div className="max-w-3xl w-full bg-white rounded-2xl shadow-sm border border-gray-100 p-8 text-center">
        
        <div className="bg-purple-50 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-6">
          <UploadCloud size={32} className="text-purple-600" />
        </div>
        
        <h1 className="text-2xl font-bold text-gray-800 mb-2">Agente de Qualificação R&E</h1>
        <p className="text-gray-500 mb-8">
          Cruza dados da web e verifica duplicidade com base de clientes/CRM.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            
            {/* INPUT 1: LEADS (OBRIGATÓRIO) */}
            <div className={`border-2 border-dashed rounded-xl p-6 relative transition-colors ${arquivoLeads ? 'bg-purple-50 border-purple-200' : 'bg-gray-50 border-gray-200 hover:bg-gray-100'}`}>
                <p className="text-sm font-bold text-gray-700 mb-2 flex items-center justify-center gap-2">
                    <FileSpreadsheet size={16}/> Lista de Leads (Obrigatório)
                </p>
                {!arquivoLeads ? (
                    <>
                        <p className="text-xs text-gray-400">Respeitar regras colunas A-E </p>
                        <input type="file" accept=".xlsx" onChange={(e) => {setArquivoLeads(e.target.files[0]); setStatus("idle")}} className="absolute inset-0 opacity-0 cursor-pointer" />
                    </>
                ) : (
                    <div className="text-purple-700 font-medium text-sm truncate px-2">
                        {arquivoLeads.name}
                        <button onClick={(e) => {e.preventDefault(); setArquivoLeads(null)}} className="ml-2 text-xs text-red-400 hover:text-red-600 underline">Remover</button>
                    </div>
                )}
            </div>

            {/* INPUT 2: CLIENTES (OPCIONAL) */}
            <div className={`border-2 border-dashed rounded-xl p-6 relative transition-colors ${arquivoClientes ? 'bg-blue-50 border-blue-200' : 'bg-gray-50 border-gray-200 hover:bg-gray-100'}`}>
                <p className="text-sm font-bold text-gray-700 mb-2 flex items-center justify-center gap-2">
                    <Database size={16}/> Base Clientes (Opcional)
                </p>
                {!arquivoClientes ? (
                    <>
                        <p className="text-xs text-gray-400">CNPJs na Coluna B</p>
                        <input type="file" accept=".xlsx" onChange={(e) => setArquivoClientes(e.target.files[0])} className="absolute inset-0 opacity-0 cursor-pointer" />
                    </>
                ) : (
                    <div className="text-blue-700 font-medium text-sm truncate px-2">
                        {arquivoClientes.name}
                        <button onClick={(e) => {e.preventDefault(); setArquivoClientes(null)}} className="ml-2 text-xs text-red-400 hover:text-red-600 underline">Remover</button>
                    </div>
                )}
            </div>
        </div>

        {/* BOTÃO DE AÇÃO */}
        <button 
            onClick={processarLista}
            disabled={!arquivoLeads || loading}
            className={`w-full py-4 rounded-xl font-bold text-lg flex items-center justify-center gap-2 transition-all ${
                loading ? 'bg-gray-100 text-gray-400 cursor-wait' :
                !arquivoLeads ? 'bg-gray-200 text-gray-400 cursor-not-allowed' :
                'bg-purple-600 hover:bg-purple-700 text-white shadow-lg hover:shadow-xl'
            }`}
        >
            {loading ? <Loader2 className="animate-spin" /> : <Play fill="currentColor" />} 
            {loading ? 'Processando Inteligência...' : 'Iniciar Qualificação'}
        </button>

        {status === 'success' && (
            <div className="mt-6 p-4 bg-green-50 text-green-700 rounded-xl flex items-center justify-center gap-2 animate-pulse">
                <CheckCircle /> Sucesso! Download iniciado.
            </div>
        )}
        {status === 'error' && (
            <div className="mt-6 p-4 bg-red-50 text-red-700 rounded-xl flex items-center justify-center gap-2">
                <AlertCircle /> Erro ao conectar. Verifique o terminal do Backend.
            </div>
        )}
      </div>
    </div>
  );
};

export default AbaQualificacao;
