"use client";

import { useState } from "react";
import { Mail, Check, AlertCircle } from "lucide-react";
import { subscribeEmail } from "@/lib/api";
import { Card } from "@/components/ui";

type Status = "idle" | "loading" | "success" | "error";

interface SubscriptionFormProps {
  variant?: "inline" | "sticky";
}

export default function SubscriptionForm({ variant = "inline" }: SubscriptionFormProps) {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<Status>("idle");
  const [message, setMessage] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus("loading");
    setMessage("");

    try {
      const result = await subscribeEmail({ email });
      setStatus("success");
      setMessage(result.message);
      setEmail("");
    } catch (error: any) {
      setStatus("error");
      setMessage(error?.message || "Failed to subscribe. Please try again.");
    }
  };

  const isSticky = variant === "sticky";

  return (
    <div className={isSticky ? "sticky top-24" : ""}>
      <Card className="bg-gradient-to-r from-slate-700 to-teal-600 text-white border-0">
        <div className="p-4 md:p-5">
          <div className="flex items-center gap-3 mb-3">
            <Mail className="w-5 h-5 flex-shrink-0" />
            <div className="flex-1">
              <h3 className="text-lg font-bold mb-1">Stay Connected</h3>
              <p className="text-teal-100 leading-relaxed text-sm">
                Get notified about new opportunities and amendments
              </p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-2">
            <div className="flex gap-2">
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Your email address"
                required
                disabled={status === "loading"}
                className="flex-1 px-3 py-2 rounded-lg bg-white text-slate-900 border border-white focus:ring-2 focus:ring-teal-300 focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed text-sm"
              />
              <button
                type="submit"
                disabled={status === "loading"}
                className="px-4 py-2 bg-white text-teal-600 font-semibold rounded-lg hover:bg-teal-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap text-sm"
              >
                {status === "loading" ? "Subscribing..." : "Subscribe"}
              </button>
            </div>

            {message && (
              <div
                className={`flex items-center gap-2 p-2 rounded-lg text-sm ${
                  status === "success"
                    ? "bg-teal-500/20 text-white"
                    : "bg-red-500/20 text-white"
                }`}
              >
                {status === "success" ? (
                  <Check className="w-4 h-4" />
                ) : (
                  <AlertCircle className="w-4 h-4" />
                )}
                <span>{message}</span>
              </div>
            )}
          </form>
        </div>
      </Card>
    </div>
  );
}

