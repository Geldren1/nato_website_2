"use client";

import { useState, useEffect } from "react";
import Hero from "@/components/shared/Hero";
import FeedbackForm from "@/components/features/feedback/FeedbackForm";
import FeedbackList from "@/components/features/feedback/FeedbackList";
import RoadmapView from "@/components/features/feedback/RoadmapView";
import { getFeedback, getRoadmap, type Feedback, type RoadmapItem } from "@/lib/api/feedback";

export default function FeedbackPage() {
  const [feedback, setFeedback] = useState<Feedback[]>([]);
  const [roadmap, setRoadmap] = useState<RoadmapItem[]>([]);
  const [isLoadingFeedback, setIsLoadingFeedback] = useState(true);
  const [isLoadingRoadmap, setIsLoadingRoadmap] = useState(true);

  const loadFeedback = async () => {
    try {
      setIsLoadingFeedback(true);
      const data = await getFeedback({ page: 1, page_size: 20 });
      setFeedback(data.items);
    } catch (error) {
      console.error("Error loading feedback:", error);
    } finally {
      setIsLoadingFeedback(false);
    }
  };

  const loadRoadmap = async () => {
    try {
      setIsLoadingRoadmap(true);
      const data = await getRoadmap();
      setRoadmap(data.items);
    } catch (error) {
      console.error("Error loading roadmap:", error);
    } finally {
      setIsLoadingRoadmap(false);
    }
  };

  useEffect(() => {
    loadFeedback();
    loadRoadmap();
  }, []);

  return (
    <>
      <Hero
        title="Beta Feedback"
        subtitle="Help us improve by reporting bugs, suggesting improvements, and tracking our roadmap"
        hideBadge={true}
      />
      
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left Column: Form */}
          <div>
            <FeedbackForm onSuccess={loadFeedback} />
          </div>

          {/* Right Column: Feedback List and Roadmap */}
          <div className="space-y-8">
            {/* Recent Feedback */}
            <div>
              <h2 className="text-2xl font-bold text-slate-900 mb-4">Recent Feedback</h2>
              <FeedbackList feedback={feedback} isLoading={isLoadingFeedback} />
            </div>

            {/* Roadmap */}
            <div>
              <h2 className="text-2xl font-bold text-slate-900 mb-4">Roadmap</h2>
              <RoadmapView roadmap={roadmap} isLoading={isLoadingRoadmap} />
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

