"use client";

import { type Feedback } from "@/lib/api/feedback";
import { Bug, Lightbulb, Clock, CheckCircle, XCircle, Loader2 } from "lucide-react";
import { Card, Badge } from "@/components/ui";
import { formatDate } from "@/lib/utils";

interface FeedbackListProps {
  feedback: Feedback[];
  isLoading?: boolean;
}

export default function FeedbackList({ feedback, isLoading }: FeedbackListProps) {
  const getStatusBadge = (status: Feedback["status"]) => {
    const variants: Record<string, "default" | "success" | "warning" | "info"> = {
      open: "info",
      in_progress: "warning",
      resolved: "success",
      rejected: "default",
    };
    return variants[status] || "default";
  };

  const getStatusIcon = (status: Feedback["status"]) => {
    switch (status) {
      case "resolved":
        return <CheckCircle className="w-4 h-4" />;
      case "rejected":
        return <XCircle className="w-4 h-4" />;
      case "in_progress":
        return <Clock className="w-4 h-4" />;
      default:
        return <Clock className="w-4 h-4" />;
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-teal-600" />
      </div>
    );
  }

  if (feedback.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-slate-600 text-lg">No feedback submitted yet</p>
        <p className="text-slate-500 text-sm mt-2">Be the first to share your thoughts!</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {feedback.map((item) => (
        <Card key={item.id} variant="elevated">
          <div className="p-4">
            <div className="flex items-start justify-between gap-3 mb-2">
              <div className="flex items-center gap-2 flex-1">
                {item.type === "bug" ? (
                  <Bug className="w-5 h-5 text-red-500 flex-shrink-0" />
                ) : (
                  <Lightbulb className="w-5 h-5 text-blue-500 flex-shrink-0" />
                )}
                <h3 className="font-semibold text-slate-900 flex-1">{item.title}</h3>
              </div>
              <Badge variant={getStatusBadge(item.status)} className="flex items-center gap-1">
                {getStatusIcon(item.status)}
                <span className="capitalize">{item.status.replace("_", " ")}</span>
              </Badge>
            </div>
            
            <p className="text-slate-600 text-sm mb-3 line-clamp-3">{item.description}</p>
            
            <div className="flex items-center justify-between text-xs text-slate-500">
              <div className="flex items-center gap-3">
                <span className="capitalize">{item.type}</span>
                {item.submitted_by && <span>• {item.submitted_by}</span>}
              </div>
              <span>{formatDate(item.submitted_at)}</span>
            </div>

            {item.resolution_notes && (
              <div className="mt-3 pt-3 border-t border-slate-200">
                <p className="text-sm text-slate-600">
                  <strong className="text-slate-900">Resolution:</strong> {item.resolution_notes}
                </p>
              </div>
            )}
          </div>
        </Card>
      ))}
    </div>
  );
}

