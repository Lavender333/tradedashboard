import React, { useEffect, useMemo, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import {
  CartesianGrid,
  ComposedChart,
  Label,
  ReferenceArea,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { Card, CardContent } from '@/components/ui/card';

type ScenarioKey = 'breakout' | 'rejection' | 'reclaim';

interface Candle {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
}

const CHART_TOP = 6800;

const candles: Candle[] = [
  { time: '09:30', open: 6580, high: 6610, low: 6570, close: 6600 },
  { time: '09:45', open: 6600, high: 6725, low: 6590, close: 6710 },
  { time: '10:00', open: 6710, high: 6755, low: 6700, close: 6720 },
  { time: '10:15', open: 6720, high: 6740, low: 6650, close: 6675 },
  { time: '10:30', open: 6675, high: 6705, low: 6660, close: 6695 },
];

type Scenario = {
  index: number;
  title: string;
  points: string[];
  tip: string;
  color: string;
};

const scenarios: Record<ScenarioKey, Scenario> = {
  breakout: {
    index: 1,
    title: 'Breakout Candle',
    points: [
      'Acceptance above 6,720 (15–30m close + hold).',
      'Entry: next candle holds above 6,720.',
      'Invalidation/Stop: ~6,705 (back inside).',
      'Targets: 6,750–6,770 then manage into 6,780–6,800.',
    ],
    tip: 'Don’t chase the first spike — let it prove acceptance before entering.',
    color: '#22c55e',
  },
  rejection: {
    index: 2,
    title: 'Rejection Candle',
    points: [
      'Probe above 6,720 but fails — long upper wick.',
      'Entry: short on failure back below 6,720 after wick.',
      'Invalidation/Stop: hold > ~6,800 (supply acceptance).',
      'Target: 6,700–6,720 first.',
    ],
    tip: 'Enter on the failure close, not on the wick itself.',
    color: '#ef4444',
  },
  reclaim: {
    index: 4,
    title: 'Reclaim Candle',
    points: [
      'Dip into 6,590–6,610 and closes back above.',
      'Entry: bullish reversal in dip zone, reclaim close.',
      'Invalidation/Stop: < 6,570 (breakdown line).',
      'Targets: 6,700–6,720 then 6,750–6,770.',
    ],
    tip: 'Look for engulfing or a long lower wick in the dip zone before entry.',
    color: '#3b82f6',
  },
};

const MESChartExplainerVideo: React.FC = () => {
  const order = useMemo<ScenarioKey[]>(() => ['breakout', 'rejection', 'reclaim'], []);
  const [active, setActive] = useState<ScenarioKey>('breakout');
  const [playing, setPlaying] = useState(true);
  const [speed, setSpeed] = useState(1);
  const [progress, setProgress] = useState(0);
  const barRef = useRef<HTMLDivElement | null>(null);
  const raf = useRef<number | null>(null);
  const lastTs = useRef<number | null>(null);
  const cycleSeconds = 5;

  const activeScenario = scenarios[active];

  const nextScenario = () => {
    const idx = order.indexOf(active);
    const next = order[(idx + 1) % order.length];
    setActive(next);
  };

  useEffect(() => {
    if (!playing) {
      return undefined;
    }

    const step = (ts: number) => {
      if (lastTs.current == null) {
        lastTs.current = ts;
      }
      const dt = (ts - (lastTs.current ?? ts)) / 1000;
      lastTs.current = ts;
      setProgress((p) => {
        const inc = (dt / (cycleSeconds / speed)) * 100;
        const nextProgress = p + inc;
        if (nextProgress >= 100) {
          nextScenario();
          return 0;
        }
        return nextProgress;
      });
      raf.current = requestAnimationFrame(step);
    };

    raf.current = requestAnimationFrame(step);

    return () => {
      if (raf.current) {
        cancelAnimationFrame(raf.current);
      }
      raf.current = null;
      lastTs.current = null;
    };
  }, [playing, speed, order, active]);

  const scrub = (clientX: number, el: HTMLDivElement | null) => {
    if (!el) {
      return;
    }
    const rect = el.getBoundingClientRect();
    const x = Math.min(Math.max(clientX - rect.left, 0), rect.width);
    const pct = (x / rect.width) * 100;
    setProgress(pct);
  };

  const renderAnimatedCandle = (candle: Candle, index: number) => {
    const isBullish = candle.close > candle.open;
    const baseColor = isBullish ? '#22c55e' : '#ef4444';
    const isHighlight = index === activeScenario.index;
    const color = isHighlight ? activeScenario.color : baseColor;
    const bodyHeight = Math.max(2, Math.abs(candle.close - candle.open));

    return (
      <motion.g
        key={index}
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: index * 0.25, duration: 0.4, ease: 'easeOut' }}
      >
        <motion.line
          x1={index * 80 + 40}
          x2={index * 80 + 40}
          y1={CHART_TOP - candle.high}
          y2={CHART_TOP - candle.low}
          stroke={color}
          strokeWidth={isHighlight ? 2 : 1}
          initial={{ scaleY: 0 }}
          animate={{ scaleY: 1 }}
          transition={{ duration: 0.3 }}
          style={{ transformOrigin: 'bottom' }}
          filter={isHighlight ? 'url(#glow)' : 'none'}
        />
        <motion.rect
          x={index * 80 + (isHighlight ? 26 : 30)}
          y={CHART_TOP - Math.max(candle.open, candle.close)}
          width={isHighlight ? 28 : 20}
          height={bodyHeight}
          fill={color}
          stroke={color}
          initial={{ height: 0 }}
          animate={{ height: bodyHeight }}
          transition={{ duration: 0.3, delay: 0.1 }}
          style={
            isHighlight ? { filter: 'drop-shadow(0 0 6px rgba(0,0,0,0.2))' } : undefined
          }
        />
        {isHighlight && (
          <motion.text
            x={index * 80 + 40}
            y={CHART_TOP - Math.max(candle.open, candle.close) - 12}
            textAnchor="middle"
            fontSize={12}
            fill={color}
            initial={{ opacity: 0, y: -6 }}
            animate={{ opacity: 1, y: 0 }}
          >
            {activeScenario.title}
          </motion.text>
        )}
      </motion.g>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white text-gray-900 p-8">
      <motion.h1
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="text-3xl font-bold text-center mb-8"
      >
        MES Chart Explainer — Breakout • Rejection • Reclaim
      </motion.h1>

      <Card className="max-w-5xl mx-auto shadow-lg border border-gray-200 rounded-2xl">
        <CardContent className="p-6">
          <div className="flex flex-wrap items-center justify-center gap-3 mb-4">
            {order.map((scenarioKey) => (
              <button
                key={scenarioKey}
                onClick={() => {
                  setActive(scenarioKey);
                  setProgress(0);
                }}
                className={`px-4 py-2 rounded-full text-sm border transition-all ${
                  active === scenarioKey
                    ? 'bg-indigo-600 text-white border-indigo-600 shadow'
                    : 'bg-white text-gray-700 border-gray-200 hover:border-gray-300'
                }`}
                aria-pressed={active === scenarioKey}
              >
                {scenarios[scenarioKey].title}
              </button>
            ))}
            <div className="h-6 w-px bg-gray-200" />
            <button
              onClick={() => setPlaying((previous) => !previous)}
              className="px-4 py-2 rounded-full text-sm border border-gray-200 bg-white hover:border-gray-300"
              aria-label={playing ? 'Pause' : 'Play'}
            >
              {playing ? 'Pause' : 'Play'}
            </button>
            <label className="text-sm text-gray-600 flex items-center gap-2">
              Speed
              <select
                className="border border-gray-200 rounded-md px-2 py-1 bg-white"
                value={speed}
                onChange={(event) => setSpeed(Number(event.target.value))}
              >
                <option value={0.5}>0.5×</option>
                <option value={0.75}>0.75×</option>
                <option value={1}>1×</option>
                <option value={1.5}>1.5×</option>
                <option value={2}>2×</option>
              </select>
            </label>
          </div>

          <div
            ref={barRef}
            className="relative h-2 w-full rounded-full bg-gray-200 overflow-hidden cursor-pointer"
            onMouseDown={(event) => {
              scrub(event.clientX, barRef.current);
              setPlaying(false);
            }}
            onMouseMove={(event) => {
              if (event.buttons === 1) {
                scrub(event.clientX, barRef.current);
              }
            }}
            onMouseUp={() => setPlaying(true)}
            aria-label="Playback progress"
          >
            <div className="absolute inset-0 bg-gradient-to-r from-indigo-200 to-indigo-300" />
            <div
              className="absolute inset-y-0 left-0 bg-indigo-600"
              style={{ width: `${progress}%` }}
            />
            <div
              className="absolute -top-1 h-4 w-4 rounded-full bg-white border border-indigo-600 shadow"
              style={{ left: `calc(${progress}% - 8px)` }}
            />
          </div>

          <div className="w-full h-96 mt-5">
            <ResponsiveContainer>
              <ComposedChart data={candles} margin={{ top: 20, right: 30, left: 20, bottom: 24 }}>
                <defs>
                  <filter id="glow">
                    <feGaussianBlur stdDeviation="1.5" result="coloredBlur" />
                    <feMerge>
                      <feMergeNode in="coloredBlur" />
                      <feMergeNode in="SourceGraphic" />
                    </feMerge>
                  </filter>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="time" tick={{ fill: '#6b7280', fontSize: 12 }} />
                <YAxis
                  domain={[6500, CHART_TOP]}
                  tickFormatter={(value) => value.toLocaleString()}
                  tick={{ fill: '#6b7280', fontSize: 12 }}
                />
                <Tooltip formatter={(value: number) => value.toLocaleString()} />

                <ReferenceArea y1={6540} y2={6560} ifOverflow="extendDomain" fill="#60a5fa" fillOpacity={0.1} />
                <ReferenceLine y={6550} stroke="#60a5fa" strokeDasharray="4 4">
                  <Label value="Demand 6,540–6,560" position="right" fill="#1d4ed8" fontSize={12} offset={8} />
                </ReferenceLine>

                <ReferenceArea y1={6590} y2={6610} ifOverflow="extendDomain" fill="#3b82f6" fillOpacity={0.08} />
                <ReferenceLine y={6600} stroke="#3b82f6" strokeDasharray="4 4">
                  <Label value="Dip Buy 6,590–6,610" position="right" fill="#1e40af" fontSize={12} offset={8} />
                </ReferenceLine>

                <ReferenceArea y1={6750} y2={6780} ifOverflow="extendDomain" fill="#f59e0b" fillOpacity={0.1} />
                <ReferenceLine y={6765} stroke="#f59e0b" strokeDasharray="4 4">
                  <Label value="Supply 6,750–6,780" position="right" fill="#b45309" fontSize={12} offset={8} />
                </ReferenceLine>

                <ReferenceLine y={6570} stroke="#ef4444" strokeDasharray="4 4">
                  <Label value="Breakdown 6,570" position="right" fill="#b91c1c" fontSize={12} offset={8} />
                </ReferenceLine>
                <ReferenceLine y={6720} stroke="#22c55e" strokeDasharray="4 4">
                  <Label value="Breakout 6,720" position="right" fill="#15803d" fontSize={12} offset={8} />
                </ReferenceLine>

                {candles.map((candle, index) => renderAnimatedCandle(candle, index))}
              </ComposedChart>
            </ResponsiveContainer>
          </div>

          <div className="mt-8 grid md:grid-cols-2 gap-6">
            <div>
              <h3 className="text-xl font-semibold text-indigo-700 mb-2">{activeScenario.title}</h3>
              <ul className="text-sm text-gray-700 space-y-2 list-disc list-inside">
                {activeScenario.points.map((point, pointIndex) => (
                  <li key={pointIndex}>{point}</li>
                ))}
              </ul>
            </div>
            <div className="rounded-xl border border-gray-200 p-4 bg-white/60">
              <p className="text-xs uppercase tracking-wide text-gray-500 mb-2">Coach’s Tip</p>
              <p className="text-sm text-gray-700">{activeScenario.tip}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default MESChartExplainerVideo;
