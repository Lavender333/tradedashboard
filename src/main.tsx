import React from 'react';
import { createRoot } from 'react-dom/client';
import TradeConditionsGraph from './TradeConditionsGraph';

const root = document.getElementById('root');
if (!root) throw new Error('Dashboard root element not found');
createRoot(root).render(
  <React.StrictMode>
    <TradeConditionsGraph />
  </React.StrictMode>
);
