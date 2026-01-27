import React from 'react';

const AbaDashboards = () => {
  return (
    <div className="h-full flex flex-col p-4">
      <h1 className="text-2xl font-bold text-gray-800 mb-4">Relatório de Origem de Vendas (BI) 📊</h1>
      <div className="flex-1 bg-white rounded-lg shadow border border-gray-200 overflow-hidden">
        {/* Substitua o src abaixo pelo Link do seu PowerBI */}
        <iframe 
            title="PowerBI Report"
            width="100%" 
            height="100%" 
            src="https://app.powerbi.com/view?r=YOUR_LINK_HERE" 
            frameBorder="0" 
            allowFullScreen={true}>
        </iframe>
      </div>
    </div>
  );
};

export default AbaDashboards;