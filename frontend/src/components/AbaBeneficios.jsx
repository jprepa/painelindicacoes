import React from 'react';
import { Check, X, Trophy, Star, Shield, Crown, Zap } from 'lucide-react';

const AbaBeneficios = () => {
  const beneficios = [
    { nome: "Divulgação no Site", bronze: true, prata: true, ouro: true, diamante: true },
    { nome: "Plano Premium + 3 Meses/Venda", bronze: true, prata: true, ouro: true, diamante: true },
    { nome: "Participação Cafés Prevision", bronze: true, prata: true, ouro: true, diamante: true },
    { nome: "Desconto p/ Cliente (MRR)", bronze: "5%", prata: "10%", ouro: "10%", diamante: "10%" },
    { nome: "Acesso a Projetos", bronze: "1 Projeto", prata: "3 Projetos", ouro: "Ilimitado", diamante: "Ilimitado" },
    { nome: "Comissão 1º MRR", bronze: false, prata: "25%", ouro: "50%", diamante: "100%" },
    { nome: "Participação em Webinar", bronze: false, prata: false, ouro: true, diamante: true },
    { nome: "Desconto na Implantação", bronze: false, prata: false, ouro: "5%", diamante: "10%" },
    { nome: "Acesso as Dashboards", bronze: false, prata: false, ouro: false, diamante: true },
    { nome: "Ingresso Construsummit", bronze: false, prata: false, ouro: false, diamante: true },
  ];

  const RenderCheck = ({ valor }) => {
    if (valor === true) return <Check className="mx-auto text-green-500" size={20} />;
    if (valor === false) return <div className="mx-auto w-2 h-2 bg-gray-200 rounded-full"></div>;
    return <span className="font-bold text-gray-700 text-sm">{valor}</span>;
  };

  return (
    <div className="h-full bg-gray-50 p-8 overflow-y-auto">
      <div className="max-w-6xl mx-auto space-y-8">
        
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold text-gray-800">Tabela de Categorias e Benefícios 🚀</h1>
          <p className="text-gray-500">Regras e recompensas do Programa de Parceiros Prevision</p>
        </div>

        {/* TABELA DE CARDS */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
          <div className="grid grid-cols-5 text-center">
            
            <div className="p-6 bg-gray-50 border-b border-gray-100 flex items-center justify-start">
              <span className="font-bold text-gray-400 uppercase tracking-wider text-xs">Benefícios</span>
            </div>

            <div className="p-6 border-b border-r border-gray-100 bg-orange-50">
              <Shield className="mx-auto text-orange-700 mb-2" size={24}/>
              <h3 className="font-bold text-orange-800">Bronze</h3>
            </div>
            <div className="p-6 border-b border-r border-gray-100 bg-gray-100">
              <Star className="mx-auto text-gray-600 mb-2" size={24}/>
              <h3 className="font-bold text-gray-800">Prata</h3>
            </div>
            <div className="p-6 border-b border-r border-gray-100 bg-yellow-50">
              <Trophy className="mx-auto text-yellow-600 mb-2" size={24}/>
              <h3 className="font-bold text-yellow-800">Ouro</h3>
            </div>
            <div className="p-6 border-b border-gray-100 bg-cyan-50 relative overflow-hidden">
              <div className="absolute top-0 right-0 bg-cyan-600 text-white text-[10px] px-2 py-0.5 rounded-bl-lg font-bold">VIP</div>
              <Crown className="mx-auto text-cyan-600 mb-2" size={24}/>
              <h3 className="font-bold text-cyan-800">Diamante</h3>
            </div>

            {beneficios.map((item, index) => (
              <React.Fragment key={index}>
                <div className="p-4 text-left text-sm font-medium text-gray-600 border-b border-gray-50 flex items-center bg-gray-50/50 px-6">
                  {item.nome}
                </div>
                <div className="p-4 border-b border-gray-50 border-r flex items-center justify-center bg-orange-50/10">
                  <RenderCheck valor={item.bronze} />
                </div>
                <div className="p-4 border-b border-gray-50 border-r flex items-center justify-center bg-gray-50/20">
                  <RenderCheck valor={item.prata} />
                </div>
                <div className="p-4 border-b border-gray-50 border-r flex items-center justify-center bg-yellow-50/10">
                  <RenderCheck valor={item.ouro} />
                </div>
                <div className="p-4 border-b border-gray-50 flex items-center justify-center bg-cyan-50/10">
                  <RenderCheck valor={item.diamante} />
                </div>
              </React.Fragment>
            ))}

          </div>
        </div>

      {/* --- CARDS DE RODAPÉ (AGORA CENTRALIZADO NA TELA) --- */}
        {/* Troquei 'grid grid-cols-3' por 'flex justify-center' */}
        <div className="flex justify-center gap-6 mt-8">
            
            <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm relative overflow-hidden flex flex-col items-center text-center max-w-md w-full">
                <div className="absolute top-0 right-0 w-16 h-16 bg-green-50 rounded-bl-full -mr-4 -mt-4"></div>
                
                <h4 className="font-bold text-gray-800 mb-2 flex items-center justify-center gap-2">
                    <Zap size={18} className="text-green-600" /> Progressão Facilitada
                </h4>
                
                <p className="text-sm text-gray-500">
                    Comece a Indicar agora mesmo e sua categoria muda rapidamente
                </p>
            </div>

        </div>
      </div>
    </div>
  );
};

export default AbaBeneficios;
