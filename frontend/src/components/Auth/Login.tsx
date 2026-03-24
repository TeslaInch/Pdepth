import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
import { BookOpen, User, Mail, Lock, Eye, EyeOff } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useToast } from "@/hooks/use-toast";
import { supabase } from "@/supabaseClient";

const Login = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.email || !formData.password) {
      toast({
        title: "Error",
        description: "Please fill in all fields.",
        variant: "destructive",
      });
      return;
    }

    const { data, error } = await supabase.auth.signInWithPassword({
      email: formData.email,
      password: formData.password,
    });

    if (error) {
      toast({
        title: "Login Failed",
        description: error.message,
        variant: "destructive",
      });
      return;
    }

    // Save token for API calls
    const session = data.session;
    localStorage.setItem("access_token", session.access_token);

    toast({
      title: "Welcome back!",
      description: "Successfully logged in to your account.",
    });

    navigate("/dashboard");
  };

  return (
    <div className="min-h-screen flex">
      {/* Left Side - Login Form */}
      <div className="flex-1 flex items-center justify-center p-8 bg-background">
        <div className="w-full max-w-md space-y-8">
          {/* Logo */}
          <div className="text-center">
            <div className="flex items-center justify-center space-x-2 mb-4">
              <div className="p-2 bg-study-gradient rounded-lg">
                <BookOpen className="h-6 w-6 text-white" />
              </div>
            </div>
            <p className="text-muted-foreground">Learn smarter, not harder</p>
          </div>

          {/* Welcome Back Header */}
          <div className="text-center space-y-2">
            <h1 className="text-3xl font-bold text-foreground">Welcome Back to PDepth</h1>
            <p className="text-muted-foreground">
              Start summarizing PDFs and watching related videos instantly
            </p>
          </div>

          {/* Login Form */}
          <Card className="shadow-card">
            <CardContent className="p-6">
              <form onSubmit={handleSubmit} className="space-y-6">
                <div className="space-y-2">
                  <Label htmlFor="email" className="text-sm font-medium">
                    Email Address
                  </Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="email"
                      type="email"
                      placeholder="Enter your email"
                      value={formData.email}
                      onChange={(e) => setFormData({...formData, email: e.target.value})}
                      className="pl-10 h-12"
                      required
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="password" className="text-sm font-medium">
                    Password
                  </Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="password"
                      type={showPassword ? "text" : "password"}
                      placeholder="Enter your password"
                      value={formData.password}
                      onChange={(e) => setFormData({...formData, password: e.target.value})}
                      className="pl-10 pr-10 h-12"
                      required
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-3 text-muted-foreground hover:text-foreground"
                    >
                      {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                </div>

                <Button 
                  type="submit" 
                  className="w-full h-12 bg-study-gradient hover:shadow-glow text-lg font-medium"
                >
                  Log In
                </Button>

                <div className="relative my-4">
                  <div className="absolute inset-0 flex items-center">
                    <span className="w-full border-t border-muted" />
                  </div>
                  <div className="relative flex justify-center text-xs uppercase">
                    <span className="bg-card px-2 text-muted-foreground">Or continue with</span>
                  </div>
                </div>

                <Button 
                  type="button" 
                  variant="outline"
                  onClick={async () => {
                    await supabase.auth.signInWithOAuth({
                      provider: 'google',
                      options: { redirectTo: window.location.origin + "/dashboard" }
                    });
                  }}
                  className="w-full h-12 text-lg font-medium"
                >
                  <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                    <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                    <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                    <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
                  </svg>
                  Google
                </Button>
              </form>
            </CardContent>
          </Card>

          {/* Sign Up Link */}
          <div className="text-center">
            <p className="text-muted-foreground">
              I do not have an account?{" "}
              <button
                onClick={() => navigate("/signup")}
                className="text-primary hover:text-primary/80 font-medium underline-offset-4 hover:underline"
              >
                Sign Up
              </button>
            </p>
          </div>
        </div>
      </div>

      {/* Right Side - Hero Section */}
      <div className="hidden lg:block flex-1 bg-hero-gradient relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-transparent via-white/10 to-transparent"></div>
        
        {/* Floating Icons */}
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
          <div className="relative">
            {/* Main Icons */}
            <div className="flex space-x-8 mb-8">
              <div className="p-6 bg-white/20 backdrop-blur-sm rounded-2xl glass-effect animate-fade-in">
                <BookOpen className="h-12 w-12 text-white" />
              </div>
              <div className="p-6 bg-white/20 backdrop-blur-sm rounded-2xl glass-effect animate-fade-in" style={{animationDelay: '0.2s'}}>
                <User className="h-12 w-12 text-white" />
              </div>
              <div className="p-6 bg-white/20 backdrop-blur-sm rounded-2xl glass-effect animate-fade-in" style={{animationDelay: '0.4s'}}>
                <BookOpen className="h-12 w-12 text-white" />
              </div>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="absolute bottom-16 left-8 right-8 text-center">
          <h2 className="text-4xl font-bold text-white mb-4">Transform Your Learning</h2>
          <p className="text-xl text-white/90 mb-8 max-w-md mx-auto">
            Upload any PDF, get instant AI-powered summaries, and discover related educational videos to deepen your understanding.
          </p>
          
          {/* Stats */}
          <div className="grid grid-cols-3 gap-6 text-center">
        
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;