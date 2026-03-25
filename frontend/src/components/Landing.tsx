import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Upload, BookOpen, Video, Download, FileText, Sparkles } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";

const Landing = () => {
  const navigate = useNavigate();

  const features = [
    {
      icon: Upload,
      title: "Instant PDF Upload",
      description: "Drag and drop your PDF files or click to browse. We support academic papers, textbooks, research documents, and more."
    },
    {
      icon: Sparkles,
      title: "AI Summarization", 
      description: "Get instant, concise summaries of your documents powered by advanced AI. Key points, main concepts, and important details all in one place."
    },
    {
      icon: Video,
      title: "Related Videos",
      description: "Watch curated YouTube videos that explain concepts from your document. Videos play directly on our platform without any distractions."
    },
    {
      icon: Download,
      title: "Export Summaries",
      description: "Download your summaries as PDF or text files. Perfect for sharing with classmates or including in your own study materials."
    }
  ];

  const steps = [
    {
      number: "1",
      title: "Upload Your PDF",
      description: "Drop your PDF here or click to browse. We support academic papers, textbooks, research documents, and more.",
      icon: FileText
    },
    {
      number: "2", 
      title: "AI Creates Summary",
      description: "Our advanced AI analyzes your document and creates a comprehensive summary highlighting key concepts, main points, and important details.",
      icon: Sparkles
    },
    {
      number: "3",
      title: "Watch Related Videos", 
      description: "Discover curated YouTube videos that explain the concepts from your document. Videos play directly on our platform without any distractions.",
      icon: Video
    }
  ];

  return (
    <div className="min-h-screen bg-background">
      {/* Navigation */}
      <nav className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-wrap justify-between items-center h-16">
            <div className="flex items-center space-x-2">
              <div className="p-2 rounded-lg">
                <img
                  src="/pdepthlogo.png"
                  alt="PDepth Logo"
                  className="h-6 w-6 object-contain"
                />
              </div>
              <span className="text-xl font-bold text-foreground">PDepth</span>
            </div>
            <div className="hidden md:flex items-center space-x-8">
              <a href="#features" className="text-muted-foreground hover:text-foreground transition-colors">Features</a>
              <a href="#how-it-works" className="text-muted-foreground hover:text-foreground transition-colors">How it Works</a>
              <a href="#pricing" className="text-muted-foreground hover:text-foreground transition-colors"></a>
            </div>
            <div className="flex items-center space-x-3 mt-2 md:mt-0">
              <Button variant="ghost" onClick={() => navigate("/login")}>
                Sign In
              </Button>
              <Button onClick={() => navigate("/signup")} className="bg-study-gradient hover:shadow-glow">
                Get Started for Free
              </Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative overflow-hidden bg-white">
        <div className="absolute"></div>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-24 lg:py-32 relative">
          <div className="text-center animate-fade-in">
            <h1 className="text-3xl sm:text-4xl md:text-6xl lg:text-7xl font-bold text-black mb-6 leading-tight break-words">
              Turn Any PDF into a<br />
              <span className="text-primary-glow">Quick Summary +</span><br />
              Related Videos
            </h1>
            <p className="text-lg sm:text-xl md:text-2xl text-black/90 mb-8 max-w-3xl mx-auto leading-relaxed">
              Upload your PDF, get a concise summary, and watch videos related to the content—all in one smart app. Perfect for students who want to learn smarter, not harder.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button 
                size="lg" 
                onClick={() => navigate("/signup")}
                className="bg-black text-white hover:bg-black/90 shadow-glow px-8 py-6 text-lg font-medium"
              >
                Get Started for Free
              </Button>
            
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-24 bg-background">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-4">
              Everything You Need to Study Smarter
            </h2>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              Our AI-powered platform combines document analysis with video learning for the ultimate study experience.
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, index) => (
              <Card key={index} className="p-6 shadow-card hover:shadow-glow transition-all duration-300 animate-fade-in" style={{animationDelay: `${index * 0.1}s`}}>
                <CardContent className="p-0">
                  <div className="p-3 bg-study-gradient rounded-lg w-fit mb-4">
                    <feature.icon className="h-6 w-6 text-white" />
                  </div>
                  <h3 className="text-xl font-semibold text-foreground mb-2">{feature.title}</h3>
                  <p className="text-muted-foreground">{feature.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="py-24 bg-muted/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-4">How It Works</h2>
            <p className="text-xl text-muted-foreground">
              Three simple steps to transform your study materials into digestible content.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
            {steps.map((step, index) => (
              <div key={step.number} className="text-center animate-fade-in" style={{animationDelay: `${index * 0.2}s`}}>
                <div className="relative mb-8">
                  <div className="w-20 h-20 bg-study-gradient rounded-full flex items-center justify-center mx-auto mb-4 shadow-glow">
                    <span className="text-2xl font-bold text-white">{step.number}</span>
                  </div>
                  <div className="p-4 bg-primary/10 rounded-full w-fit mx-auto">
                    <step.icon className="h-8 w-8 text-primary" />
                  </div>
                </div>
                <h3 className="text-2xl font-semibold text-foreground mb-4">{step.title}</h3>
                <p className="text-muted-foreground text-lg leading-relaxed">{step.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 bg-hero-gradient relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent"></div>
        <div className="max-w-4xl mx-auto text-center px-4 sm:px-6 lg:px-8 relative">
          <h2 className="text-3xl md:text-5xl font-bold text-white mb-6">
            Ready to Learn Smarter, Not Harder?
          </h2>
          <p className="text-xl text-white/90 mb-8">
            Join our community of students who are already using PDepth to ace their studies. Start for free today!
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button 
              size="lg"
              onClick={() => navigate("/signup")}
              className="bg-white text-primary hover:bg-white/90 shadow-glow px-8 py-6 text-lg font-medium"
            >
              Upload Your First PDF
            </Button>
      
          </div>
        </div>
      </section>

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
            <div className="flex space-x-8 text-muted-foreground w-full justify-center md:justify-end">
              <a href="#" className="hover:text-foreground transition-colors">About</a>
              
              <Dialog>
                <DialogTrigger asChild>
                  <button className="hover:text-foreground transition-colors">Privacy</button>
                </DialogTrigger>
                <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
                  <DialogHeader>
                    <DialogTitle>Privacy Policy</DialogTitle>
                  </DialogHeader>
                  <div className="text-sm text-muted-foreground whitespace-pre-wrap">
                    {"Your privacy is important to us. This Privacy Policy explains how we collect, use, and protect your information when you use PDepth.\n\n1. Information We Collect\nWe collect information you provide directly to us (like your name and email) and automatically collected information (like usage data).\n\n2. How We Use Your Information\nWe use the information to provide, maintain, and improve our services, communicate with you, and personalize your experience.\n\n3. Data Security\nWe implement reasonable security measures to protect your information, but remember that no method of transmission over the internet is 100% secure.\n\nFor full details, contact our support."}
                  </div>
                </DialogContent>
              </Dialog>

              <Dialog>
                <DialogTrigger asChild>
                  <button className="hover:text-foreground transition-colors">Terms</button>
                </DialogTrigger>
                <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
                  <DialogHeader>
                    <DialogTitle>Terms of Service</DialogTitle>
                  </DialogHeader>
                  <div className="text-sm text-muted-foreground whitespace-pre-wrap">
                    {"Welcome to PDepth. By using our service, you agree to these terms.\n\n1. Acceptance of Terms\nBy accessing our service, you agree to be bound by these Terms of Service.\n\n2. User Accounts\nYou are responsible for maintaining the security of your account and password.\n\n3. Acceptable Use\nYou agree not to misuse the service or help anyone else do so. You must not upload illegal or infringing content.\n\n4. Subscriptions\nPaid plans are billed as described during checkout. You may cancel at any time.\n\n5. Limitation of Liability\nOur service is provided 'as is'. We are not liable for damages arising from your use of the service."}
                  </div>
                </DialogContent>
              </Dialog>

              <a href="#" className="hover:text-foreground transition-colors">Contact</a>
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

export default Landing;