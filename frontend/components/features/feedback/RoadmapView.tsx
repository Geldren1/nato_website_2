"use client";

import { type RoadmapItem } from "@/lib/api/feedback";
import { Sparkles, Wrench, CheckCircle, Clock, XCircle, Loader2 } from "lucide-react";
import { Card, Badge } from "@/components/ui";
import { formatDate } from "@/lib/utils";

interface RoadmapViewProps {
  roadmap: RoadmapItem[];
  isLoading?: boolean;
}

export default function RoadmapView({ roadmap, isLoading }: RoadmapViewProps) {
  const getStatusBadge = (status: RoadmapItem["status"]) => {
    const variants: Record<string, "default" | "success" | "warning" | "info"> = {
      planned: "default",
      in_progress: "warning",
      completed: "success",
      cancelled: "default",
    };
    return variants[status] || "default";
  };

  const getStatusIcon = (status: RoadmapItem["status"]) => {
    switch (status) {
      case "completed":
        return <CheckCircle className="w-4 h-4" />;
      case "cancelled":
        return <XCircle className="w-4 h-4" />;
      case "in_progress":
        return <Clock className="w-4 h-4" />;
      default:
        return <Clock className="w-4 h-4" />;
    }
  };

  const getCategoryIcon = (category: RoadmapItem["category"]) => {
    return category === "new_feature" ? (
      <Sparkles className="w-5 h-5 text-purple-500" />
    ) : (
      <Wrench className="w-5 h-5 text-blue-500" />
    );
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-teal-600" />
      </div>
    );
  }

  if (roadmap.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-slate-600 text-lg">No roadmap items yet</p>
        <p className="text-slate-500 text-sm mt-2">Check back soon for updates!</p>
      </div>
    );
  }

  // Group by status
  const grouped = roadmap.reduce((acc, item) => {
    if (!acc[item.status]) {
      acc[item.status] = [];
    }
    acc[item.status].push(item);
    return acc;
  }, {} as Record<string, RoadmapItem[]>);

  const statusOrder = ["in_progress", "planned", "completed", "cancelled"];
  const statusLabels: Record<string, string> = {
    in_progress: "In Progress",
    planned: "Planned",
    completed: "Completed",
    cancelled: "Cancelled",
  };

  return (
    <div className="space-y-6">
      {statusOrder.map((status) => {
        const items = grouped[status];
        if (!items || items.length === 0) return null;

        return (
          <div key={status}>
            <h3 className="text-lg font-semibold text-slate-900 mb-3 capitalize">
              {statusLabels[status] || status.replace("_", " ")}
            </h3>
            <div className="space-y-3">
              {items.map((item) => (
                <Card key={item.id} variant="elevated">
                  <div className="p-4">
                    <div className="flex items-start justify-between gap-3 mb-2">
                      <div className="flex items-center gap-2 flex-1">
                        {getCategoryIcon(item.category)}
                        <h4 className="font-semibold text-slate-900">{item.title}</h4>
                      </div>
                      <Badge variant={getStatusBadge(item.status)} className="flex items-center gap-1">
                        {getStatusIcon(item.status)}
                        <span className="capitalize">{item.status.replace("_", " ")}</span>
                      </Badge>
                    </div>
                    
                    {item.description && (
                      <p className="text-slate-600 text-sm mb-3">{item.description}</p>
                    )}
                    
                    <div className="flex items-center justify-between text-xs text-slate-500">
                      <span className="capitalize">{item.category.replace("_", " ")}</span>
                      {item.target_date && (
                        <span>Target: {formatDate(item.target_date)}</span>
                      )}
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}

