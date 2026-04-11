import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { supabase } from "../lib/supabase";
import type { Lead, LeadStatus } from "../types";
import { PIPELINE_STATUSES, STATUS_LABELS, STATUS_HEX, STATUS_COLORS } from "../types";

export default function Pipeline() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [dragging, setDragging] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState<LeadStatus | null>(null);
  const navigate = useNavigate();

  useEffect(() => { fetchLeads(); }, []);

  async function fetchLeads() {
    const { data } = await supabase.from("leads").select("*").order("updated_at", { ascending: false });
    setLeads(data ?? []);
    setLoading(false);
  }

  async function moveToStatus(leadId: string, newStatus: LeadStatus) {
    await supabase.from("leads").update({ status: newStatus }).eq("id", leadId);
    setLeads((prev) => prev.map((l) => (l.id === leadId ? { ...l, status: newStatus } : l)));
  }

  const grouped = PIPELINE_STATUSES.reduce((acc, s) => {
    acc[s] = leads.filter((l) => l.status === s);
    return acc;
  }, {} as Record<LeadStatus, Lead[]>);

  const descartados = leads.filter((l) => l.status === "descartado");
  const totalActive = leads.length - descartados.length;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="w-5 h-5 border-2 border-violet border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="px-8 pt-7 pb-5 flex items-end justify-between border-b border-edge-subtle">
        <div>
          <h1 className="font-serif text-3xl text-bright italic tracking-tight">Pipeline</h1>
          <p className="text-dim text-xs mt-1.5 tracking-wide">
            {totalActive} lead{totalActive !== 1 ? "s" : ""} ativo{totalActive !== 1 ? "s" : ""}
            {descartados.length > 0 && (
              <span className="text-dim/60"> &middot; {descartados.length} descartado{descartados.length > 1 ? "s" : ""}</span>
            )}
          </p>
        </div>
        {/* Mini summary */}
        <div className="flex gap-4 mb-1">
          {PIPELINE_STATUSES.map((s) => (
            <div key={s} className="text-center">
              <p className="text-lg font-bold text-bright leading-none" style={{ color: STATUS_HEX[s] }}>
                {grouped[s]?.length ?? 0}
              </p>
              <p className="text-[9px] text-dim uppercase tracking-widest mt-1">{STATUS_LABELS[s]}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Kanban */}
      <div className="flex-1 flex gap-0 overflow-x-auto pipeline-scroll">
        {PIPELINE_STATUSES.map((status, colIdx) => {
          const items = grouped[status];
          const isOver = dragOver === status;
          const hex = STATUS_HEX[status];
          const colors = STATUS_COLORS[status];

          return (
            <div
              key={status}
              className={`flex-1 min-w-[230px] flex flex-col border-r border-edge-subtle last:border-r-0 transition-colors duration-200 ${
                isOver ? "col-drop-active" : ""
              }`}
              onDragOver={(e) => { e.preventDefault(); setDragOver(status); }}
              onDragLeave={() => setDragOver(null)}
              onDrop={() => { if (dragging) moveToStatus(dragging, status); setDragging(null); setDragOver(null); }}
            >
              {/* Column header */}
              <div className="px-4 py-3 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full" style={{ background: hex }} />
                  <span className="text-xs font-semibold text-sub uppercase tracking-wider">
                    {STATUS_LABELS[status]}
                  </span>
                </div>
                <span className="text-[11px] font-bold text-dim tabular-nums">
                  {items.length}
                </span>
              </div>

              {/* Accent line */}
              <div className="mx-4 h-px mb-1" style={{ background: `linear-gradient(90deg, ${hex}40, transparent)` }} />

              {/* Cards */}
              <div className="flex-1 overflow-y-auto px-3 pb-3 pt-2 space-y-2">
                {items.map((lead, i) => (
                  <div
                    key={lead.id}
                    draggable
                    onDragStart={() => setDragging(lead.id)}
                    onDragEnd={() => { setDragging(null); setDragOver(null); }}
                    onClick={() => navigate(`/lead/${lead.id}`)}
                    className={`stagger-in card-lift bg-surface border border-edge-subtle rounded-lg p-3 cursor-pointer group ${
                      dragging === lead.id ? "opacity-30 scale-[0.97]" : ""
                    }`}
                    style={{ animationDelay: `${colIdx * 50 + i * 30}ms` }}
                  >
                    {/* Name */}
                    <p className="text-[13px] font-semibold text-bright truncate leading-snug">
                      {lead.nome_loja || `@${lead.instagram}`}
                    </p>

                    {/* Handle */}
                    <p className="text-[11px] text-dim mt-0.5 truncate">
                      @{lead.instagram}
                    </p>

                    {/* Footer */}
                    <div className="flex items-center justify-between mt-2.5 pt-2 border-t border-edge-subtle/60">
                      <span className="text-[10px] text-dim font-medium tabular-nums">
                        {lead.seguidores > 0 ? `${(lead.seguidores / 1000).toFixed(1)}k` : "—"}
                      </span>
                      <svg
                        className="w-3 h-3 text-edge group-hover:text-violet transition-colors"
                        fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                      </svg>
                    </div>
                  </div>
                ))}

                {items.length === 0 && (
                  <div className={`rounded-lg border border-dashed py-10 text-center transition-all duration-200 ${
                    isOver ? "border-violet/30 bg-violet/5" : "border-edge-subtle"
                  }`}>
                    <p className="text-[11px] text-dim">{isOver ? "Soltar aqui" : "Vazio"}</p>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
