import { motion } from 'framer-motion';
import { Cpu, GitBranch, Info } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';

const qaoa_steps = [
  { step: 1, title: 'Candidate generation', desc: 'Generate up to eight unique, feasible routes with classical graph search.' },
  { step: 2, title: 'One-hot QUBO', desc: 'Assign one binary variable to each candidate and penalize invalid selections.' },
  { step: 3, title: 'Parameterized circuit', desc: 'Build a p-layer QAOA ansatz for the candidate-selection Hamiltonian.' },
  { step: 4, title: 'COBYLA optimization', desc: 'Optimize γ and β against measurements from the Aer simulator.' },
  { step: 5, title: 'Feasible decoding', desc: 'Decode measured bitstrings and report probability, counts, and fallback state.' },
];

export default function QuantumEnginePage() {
  return (
    <div className="space-y-6">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-2xl font-bold">Quantum Engine</h1>
        <p className="text-sm text-muted-foreground mt-0.5">QAOA implementation details and quantum circuit visualization</p>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* QAOA Overview */}
        <div className="lg:col-span-2 space-y-6">
          <Card glass>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Cpu className="w-4 h-4 text-purple-400" />
                <CardTitle>QAOA Pipeline</CardTitle>
                <Badge variant="purple">IBM Qiskit Simulator</Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {qaoa_steps.map((s, i) => (
                  <motion.div
                    key={s.step}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.1 }}
                    className="flex gap-4 p-3 rounded-lg bg-background/50 border border-border"
                  >
                    <div className="w-8 h-8 rounded-full bg-purple-500/20 border border-purple-500/30 flex items-center justify-center shrink-0">
                      <span className="text-xs font-bold text-purple-400">{s.step}</span>
                    </div>
                    <div>
                      <p className="text-sm font-medium">{s.title}</p>
                      <p className="text-xs text-muted-foreground mt-0.5">{s.desc}</p>
                    </div>
                    <Badge variant="info" className="ml-auto shrink-0 self-start">Implemented</Badge>
                  </motion.div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* QUBO Formulation */}
          <Card glass>
            <CardHeader>
              <div className="flex items-center gap-2">
                <GitBranch className="w-4 h-4 text-blue-400" />
                <CardTitle>QUBO Formulation</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <div className="p-4 rounded-lg bg-background/80 border border-border font-mono text-sm space-y-2">
                <p className="text-purple-400"># One binary variable per feasible candidate route</p>
                <p className="text-blue-300">E(x) = Σ<sub>i</sub> c<sub>i</sub>x<sub>i</sub> + 2(Σ<sub>i</sub>x<sub>i</sub> − 1)²</p>
                <p className="text-muted-foreground mt-2"># Guarantees:</p>
                <p className="text-cyan-300">  - Candidate paths already satisfy connectivity and endpoints</p>
                <p className="text-cyan-300">  - Penalty rejects zero or multiple selected routes</p>
                <p className="text-cyan-300">  - Costs use the same normalized objective as classical solvers</p>
                <p className="text-muted-foreground mt-2"># QAOA Ansatz:</p>
                <p className="text-emerald-300">  |ψ(γ,β)⟩ = e<sup>-iβH_B</sup> e<sup>-iγH_C</sup> |+⟩<sup>⊗n</sup></p>
              </div>
              <div className="mt-4 p-3 rounded-lg bg-blue-500/5 border border-blue-500/20 flex gap-2">
                <Info className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
                <p className="text-xs text-muted-foreground">
                  This release uses QAOA as a bounded candidate selector. The exact classical optimum is included,
                  so the experiment measures selection quality and overhead rather than claiming quantum advantage.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Sidebar Info */}
        <div className="space-y-4">
          <Card glass>
            <CardHeader><CardTitle className="text-sm">Quantum Parameters</CardTitle></CardHeader>
            <CardContent className="space-y-3">
              {[
                { label: 'Backend', value: 'Qiskit Aer Simulator' },
                { label: 'Algorithm', value: 'QAOA' },
                { label: 'Optimizer', value: 'COBYLA' },
                { label: 'QAOA Layers (p)', value: '1–5' },
                { label: 'Max Iterations', value: '80 default' },
                { label: 'Shot Count', value: '1024' },
              ].map((p) => (
                <div key={p.label} className="flex justify-between text-sm">
                  <span className="text-muted-foreground">{p.label}</span>
                  <span className="font-mono text-foreground">{p.value}</span>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card glass>
            <CardHeader><CardTitle className="text-sm">Disclaimer</CardTitle></CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground leading-relaxed">
                This system uses a shot-based Qiskit Aer simulator, not quantum hardware. Classical graph
                algorithms are expected to be faster and exact for this small routing graph. No quantum advantage is claimed.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
