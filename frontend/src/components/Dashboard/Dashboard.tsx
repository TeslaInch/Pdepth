import { useState } from "react";
import { useNavigate } from 'react-router-dom';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  BookOpen,
  Clock,
  FileText,
  LogOut,
  Menu,
  MessageSquare,
  Play,
  Search,
  Settings,
  User,
  X,
} from "lucide-react";
import PDFUpload from "./PDFUpload";
import SummaryCard from "./SummaryCard";
import VideoCard from "./VideoCard";
import { supabase } from "@/supabaseClient";



const Dashboard = () => {
  const [selectedTab, setSelectedTab] = useState("dashboard");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [expandedSummaries, setExpandedSummaries] = useState<Set<number>>(new Set());

  const [summaries, setSummaries] = useState<any[]>([]);
  const [videos, setVideos] = useState<any[]>([]);

   const navigate = useNavigate();

const handleLogout = async () => {
  await supabase.auth.signOut();
  localStorage.removeItem("access_token");
  navigate('/login');
};

  const handleTabChange = (tab: string) => {
    setSelectedTab(tab);
    setSidebarOpen(false);
  };

  // Toggle expanded view for summaries
  const toggleSummaryExpanded = (summaryId: number) => {
    const newExpanded = new Set(expandedSummaries);
    if (newExpanded.has(summaryId)) {
      newExpanded.delete(summaryId);
    } else {
      newExpanded.add(summaryId);
    }
    setExpandedSummaries(newExpanded);
  };

  // Create extended details for a summary (mock data - you can enhance this)
  const getExtendedDetails = (summary: any) => {
    return {
      fullSummary: summary.summary, // Use the actual summary as the full summary
      keyPoints: summary.summary.split('.').filter(point => point.trim().length > 20).slice(0, 5).map(point => point.trim() + '.'),
      readingTime: "",
      pageCount: 1,// Random page count - you can get this from PDF metadata
      difficulty: ""
    };
  };

  // Handle successful PDF upload and processing
  const handleUploadComplete = (result: any) => {
    console.log("PDF processing completed:", result);
    
    if (result.summary) {
      // Create summary object
      const summaryObj = {
        id: Date.now() + Math.random(),
        title: result.filename.replace('.pdf', ''),
        summary: result.summary,
        uploadDate: result.upload_date || new Date().toISOString(),
        processingStatus: "completed",
        author: "Unknown", // You can extract this from PDF metadata if needed
      };

      // Update state with summary
      setSummaries(prev => [...prev, summaryObj]);

      // Handle videos - FIXED: Use result.videos instead of result.data
      if (result.videos && Array.isArray(result.videos) && result.videos.length > 0) {
        const formattedVideos = result.videos.map((video: any, index: number) => ({
          id: Date.now() + index + Math.random(),
          title: video.title || "Video Title",
          channel: video.channel || "Unknown Channel",
          duration: video.duration || "0:00",
          thumbnail: video.thumbnail || "",
          url: video.url || "#"
        }));
        setVideos(prev => [...prev, ...formattedVideos]);
      } else {
        console.log("No videos found in result:", result.videos);
      }
    }
  };

return (
  <div className="min-h-screen bg-background">
    {/* Top Navigation */}
    <nav className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center space-x-2">
            <Button
              variant="ghost"
              size="sm"
              className="lg:hidden"
              onClick={() => setSidebarOpen(!sidebarOpen)}
            >
              {sidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </Button>
            <div className="p-2 rounded-lg">
              <img src="/pdepthlogo.png" alt="PDepth Logo" className="h-6 w-6 object-contain" />
            </div>
            <span className="text-xl font-bold text-foreground">PDepth</span>
          </div>

          <div className="flex items-center space-x-4">
            <Button
              variant="ghost"
              size="sm"
              className="hidden sm:flex"
              onClick={() => window.open('https://tally.so/r/wgBjeO', '_blank')}
            >
              <MessageSquare className="h-4 w-4" />
            </Button>
            <Button variant="ghost" size="sm" onClick={handleLogout}>
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </nav>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex gap-8 relative">
          {sidebarOpen && <div className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden" onClick={() => setSidebarOpen(false)} />}
          
          {/* Sidebar Navigation */}
          <div
            className={`w-64 space-y-2 lg:relative lg:translate-x-0 fixed left-0 top-16 h-[calc(100vh-4rem)] z-50 bg-background transform transition-transform duration-200 ease-in-out ${
              sidebarOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
            }`}
          >
            <div className="p-4 bg-card rounded-lg border shadow-sm m-4 lg:m-0">
              <nav className="space-y-1">
                {["dashboard","my-pdfs","summaries","videos"].map((tab) => {
                  const icons: { [key: string]: React.ComponentType<{ className?: string }> } = { 
                    dashboard: BookOpen, 
                    "my-pdfs": FileText, 
                    summaries: Clock, 
                    videos: Play 
                  };
                  const IconComponent = icons[tab];
                  return (
                    <button
                      key={tab}
                      onClick={() => handleTabChange(tab)}
                      className={`w-full flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                        selectedTab === tab
                          ? "bg-primary text-primary-foreground"
                          : "text-muted-foreground hover:text-foreground hover:bg-muted"
                      }`}
                    >
                      <IconComponent className="mr-3 h-4 w-4" />
                      {tab.charAt(0).toUpperCase() + tab.slice(1).replace("-", " ")}
                    </button>
                  );
                })}
              </nav>
            </div>
          </div>

          {/* Main Content */}
          <div className="flex-1 lg:ml-0">
            {selectedTab === "dashboard" && (
              <div className="space-y-8">
                {/* Upload Section */}
                <div className="bg-hero-gradient rounded-2xl p-8 text-white">
                  <div className="max-w-2xl">
                    <h1 className="text-3xl font-bold mb-2">Upload Your PDF</h1>
                    <p className="text-white/90 mb-6">
                      Drag and drop your PDF files or click to browse. Get instant AI-powered summaries and related video content—all in one smart app.
                    </p>
                    <PDFUpload onUploadComplete={handleUploadComplete} />
                  </div>
                </div>

                {/* Recent Activity */}
                <div className="grid grid-cols-1 lg:grid-cols-1 gap-8">
                  {summaries.length > 0 && (
                    <Card className="shadow-card">
                      <CardHeader>
                        <CardTitle className="flex items-center">
                          <FileText className="mr-2 h-5 w-5" />
                          Latest Summary
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <SummaryCard 
                          pdf={summaries[summaries.length - 1]} 
                          expanded={expandedSummaries.has(summaries[summaries.length - 1]?.id)}
                          onViewDetails={() => toggleSummaryExpanded(summaries[summaries.length - 1]?.id)}
                          extendedDetails={expandedSummaries.has(summaries[summaries.length - 1]?.id) ? getExtendedDetails(summaries[summaries.length - 1]) : undefined}
                        />
                      </CardContent>
                    </Card>
                  )}

                  {videos.length > 0 && (
                    <Card className="shadow-card">
                      <CardHeader>
                        <CardTitle className="flex items-center">
                          <Play className="mr-2 h-5 w-5" />
                          Related Videos
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        {videos.slice(-3).map((video) => (
                          <VideoCard key={video.id} video={video} />
                        ))}
                      </CardContent>
                    </Card>
                  )}
                </div>

                {/* Empty State */}
                {summaries.length === 0 && (
                  <div className="text-center py-12">
                    <FileText className="h-16 w-16 mx-auto text-gray-300 mb-4" />
                    <h3 className="text-xl font-medium text-gray-900 mb-2">No PDFs processed yet</h3>
                    <p className="text-gray-500">Upload your first PDF to see summaries and video recommendations here.</p>
                  </div>
                )}
              </div>
            )}

            {selectedTab === "my-pdfs" && (
              <div className="space-y-6">
                <div className="flex justify-between items-center">
                  <h2 className="text-2xl font-bold text-foreground">My PDFs</h2>
                  <Badge variant="secondary">{summaries.length} documents</Badge>
                </div>
                <div className="grid gap-6">
                  {summaries.map((summary) => (
                    <SummaryCard 
                      key={summary.id} 
                      pdf={summary} 
                      expanded={expandedSummaries.has(summary.id)}
                      onViewDetails={() => toggleSummaryExpanded(summary.id)}
                      extendedDetails={expandedSummaries.has(summary.id) ? getExtendedDetails(summary) : undefined}
                    />
                  ))}
                  {summaries.length === 0 && (
                    <div className="text-center py-12 text-gray-500">
                      <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
                      <p>No PDFs uploaded yet. Upload your first PDF to get started!</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {selectedTab === "summaries" && (
              <div className="space-y-6">
                <div className="flex justify-between items-center">
                  <h2 className="text-2xl font-bold text-foreground">All Summaries</h2>
                  <Badge variant="secondary">
                    {summaries.filter((p) => p.processingStatus === "completed").length} completed
                  </Badge>
                </div>
                <div className="grid gap-6">
                  {summaries
                    .filter((summary) => summary.processingStatus === "completed")
                    .map((summary) => (
                      <SummaryCard 
                        key={summary.id} 
                        pdf={summary} 
                        expanded={expandedSummaries.has(summary.id)}
                        onViewDetails={() => toggleSummaryExpanded(summary.id)}
                        extendedDetails={expandedSummaries.has(summary.id) ? getExtendedDetails(summary) : undefined}
                      />
                    ))}
                  {summaries.filter(s => s.processingStatus === "completed").length === 0 && (
                    <div className="text-center py-12 text-gray-500">
                      <Clock className="h-12 w-12 mx-auto mb-4 opacity-50" />
                      <p>No completed summaries yet. Upload and process PDFs to see summaries here!</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {selectedTab === "videos" && (
              <div className="space-y-6">
                <div className="flex justify-between items-center">
                  <h2 className="text-2xl font-bold text-foreground">Related Videos</h2>
                  <Badge variant="secondary">{videos.length} videos</Badge>
                </div>
                <div className="grid gap-4">
                  {videos.map((video) => (
                    <VideoCard key={video.id} video={video} expanded />
                  ))}
                  {videos.length === 0 && (
                    <div className="text-center py-12 text-gray-500">
                      <Play className="h-12 w-12 mx-auto mb-4 opacity-50" />
                      <p>No video recommendations yet. Upload and process PDFs to get related videos!</p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
      {/* Footer */}
      <footer className="bg-background border-t py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="flex items-center space-x-2 mb-4 md:mb-0">
              <div className="p-2 bg-study-gradient rounded-lg">
                <BookOpen className="h-5 w-5 text-white" />
              </div>
              <span className="text-lg font-bold text-foreground">PDepth</span>
            </div>
            <div className="flex space-x-8 text-muted-foreground">
              <a href="https://tally.so/r/wgBjeO" className="hover:text-foreground transition-colors">Feedback</a>
            </div>
          </div>
          <div className="mt-8 pt-8 border-t text-center text-muted-foreground">
            <p>&copy; {new Date().getFullYear()} PDepth. All rights reserved. Made for students worldwide.</p>
          </div>
        </div>
      </footer>
    </div>
    
  );
};

export default Dashboard;