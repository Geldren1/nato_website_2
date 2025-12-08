"use client";

import { useState } from "react";
import { Bug, Lightbulb, Send, Check, AlertCircle } from "lucide-react";
import { createFeedback, type FeedbackCreate } from "@/lib/api/feedback";
import { Card } from "@/components/ui";

type Status = "idle" | "loading" | "success" | "error";

interface FeedbackFormProps {
  onSuccess?: () => void;
}

export default function FeedbackForm({ onSuccess }: FeedbackFormProps) {
  const [type, setType] = useState<"bug" | "improvement">("bug");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [submittedBy, setSubmittedBy] = useState("");
  const [status, setStatus] = useState<Status>("idle");
  const [message, setMessage] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus("loading");
    setMessage("");

    try {
      const feedbackData: FeedbackCreate = {
        type,
        title: title.trim(),
        description: description.trim(),
        submitted_by: submittedBy.trim() || null,
      };

      await createFeedback(feedbackData);
      setStatus("success");
      setMessage("Thank you! Your feedback has been submitted.");
      
      // Reset form
      setTitle("");
      setDescription("");
      setSubmittedBy("");
      
      // Call success callback to refresh list
      if (onSuccess) {
        setTimeout(() => {
          onSuccess();
          setStatus("idle");
          setMessage("");
        }, 2000);
      } else {
        setTimeout(() => {
          setStatus("idle");
          setMessage("");
        }, 3000);
      }
    } catch (error: any) {
      setStatus("error");
      setMessage(error?.message || "Failed to submit feedback. Please try again.");
    }
  };

  return (
    <Card variant="elevated">
      <div className="p-6">
        <h2 className="text-2xl font-bold text-slate-900 mb-4">Report an Issue / Suggest an Improvement</h2>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Type Selection */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Type
            </label>
            <div className="flex gap-3">
              <button
                type="button"
                onClick={() => setType("bug")}
                className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg border-2 transition-all ${
                  type === "bug"
                    ? "border-red-500 bg-red-50 text-red-700"
                    : "border-slate-200 bg-white text-slate-600 hover:border-slate-300"
                }`}
              >
                <Bug className="w-5 h-5" />
                <span className="font-medium">Bug Report</span>
              </button>
              <button
                type="button"
                onClick={() => setType("improvement")}
                className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg border-2 transition-all ${
                  type === "improvement"
                    ? "border-blue-500 bg-blue-50 text-blue-700"
                    : "border-slate-200 bg-white text-slate-600 hover:border-slate-300"
                }`}
              >
                <Lightbulb className="w-5 h-5" />
                <span className="font-medium">Improvement</span>
              </button>
            </div>
          </div>

          {/* Title */}
          <div>
            <label htmlFor="title" className="block text-sm font-medium text-slate-700 mb-2">
              Title <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              id="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Brief description of the issue or improvement"
              required
              maxLength={200}
              disabled={status === "loading"}
              className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
            />
          </div>

          {/* Description */}
          <div>
            <label htmlFor="description" className="block text-sm font-medium text-slate-700 mb-2">
              Description <span className="text-red-500">*</span>
            </label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Please provide detailed information..."
              required
              rows={5}
              disabled={status === "loading"}
              className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed resize-y"
            />
          </div>

          {/* Submitted By (Optional) */}
          <div>
            <label htmlFor="submitted_by" className="block text-sm font-medium text-slate-700 mb-2">
              Your Email or Name (Optional)
            </label>
            <input
              type="text"
              id="submitted_by"
              value={submittedBy}
              onChange={(e) => setSubmittedBy(e.target.value)}
              placeholder="email@example.com or Your Name"
              maxLength={255}
              disabled={status === "loading"}
              className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
            />
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={status === "loading" || !title.trim() || !description.trim()}
            className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-gradient-to-r from-slate-700 to-teal-600 text-white font-semibold rounded-lg hover:from-slate-800 hover:to-teal-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {status === "loading" ? (
              <>
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Submitting...</span>
              </>
            ) : (
              <>
                <Send className="w-5 h-5" />
                <span>Submit Feedback</span>
              </>
            )}
          </button>

          {/* Status Message */}
          {message && (
            <div
              className={`flex items-center gap-2 p-3 rounded-lg ${
                status === "success"
                  ? "bg-green-50 text-green-700 border border-green-200"
                  : "bg-red-50 text-red-700 border border-red-200"
              }`}
            >
              {status === "success" ? (
                <Check className="w-5 h-5 flex-shrink-0" />
              ) : (
                <AlertCircle className="w-5 h-5 flex-shrink-0" />
              )}
              <span className="text-sm">{message}</span>
            </div>
          )}
        </form>
      </div>
    </Card>
  );
}

