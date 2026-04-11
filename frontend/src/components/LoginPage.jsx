import { useState } from "react";
import { motion } from "motion/react";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { Separator } from "./ui/separator";
import { Checkbox } from "./ui/checkbox";
import { ThemeToggle } from "./ThemeToggle.jsx";
import { ImageWithFallback } from "./figma/ImageWithFallback.jsx";
import {
  Sparkles,
  Mail,
  Lock,
  ArrowLeft,
  Chrome,
  Github,
  Linkedin,
  Eye,
  EyeOff,
} from "lucide-react";

export function LoginPage({ onBack, onLogin, onSignup, onForgot }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    onLogin();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-secondary/10 dark:from-background dark:via-background dark:to-secondary/10">
      {/* Header */}
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 dark:bg-background/95 dark:border-border">
        <div className="container flex h-16 items-center justify-between px-4">
          <div className="flex items-center gap-2">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-chart-1 to-chart-3">
              <Sparkles className="h-5 w-5 text-white" />
            </div>
            <span className="text-lg text-foreground">LearnPath AI</span>
          </div>
          
          <ThemeToggle />
        </div>
      </header>

      <div className="container px-4 py-12">
        <div className="grid lg:grid-cols-2 gap-12 items-center max-w-6xl mx-auto">
          {/* Left Side - Form */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5 }}
            className="w-full max-w-md mx-auto lg:mx-0"
          >
            <Button
              variant="ghost"
              onClick={onBack}
              className="mb-6 gap-2 text-foreground dark:text-foreground hover:bg-accent/50 dark:hover:bg-accent/50"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to Home
            </Button>

            <Card className="shadow-lg border-border/50 bg-card dark:bg-card">
              <CardHeader className="space-y-1">
                <CardTitle className="text-2xl text-foreground dark:text-foreground">Welcome Back</CardTitle>
                <CardDescription className="text-muted-foreground dark:text-muted-foreground">
                  Enter your credentials to access your account
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <form onSubmit={handleSubmit} className="space-y-4">
                  {/* Email */}
                  <div className="space-y-2">
                    <Label htmlFor="email" className="text-foreground dark:text-foreground">Email</Label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground dark:text-muted-foreground" />
                      <Input
                        id="email"
                        type="email"
                        placeholder="name@example.com"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        className="pl-10 bg-input-background dark:bg-input-background dark:text-foreground dark:placeholder:text-muted-foreground border-border/50 dark:border-border/50"
                        required
                      />
                    </div>
                  </div>

                  {/* Password */}
                  <div className="space-y-2">
                    <Label htmlFor="password" className="text-foreground dark:text-foreground">Password</Label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground dark:text-muted-foreground" />
                      <Input
                        id="password"
                        type={showPassword ? "text" : "password"}
                        placeholder="••••••••"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        className="pl-10 pr-10 bg-input-background dark:bg-input-background dark:text-foreground dark:placeholder:text-muted-foreground border-border/50 dark:border-border/50"
                        required
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground dark:text-muted-foreground dark:hover:text-foreground"
                      >
                        {showPassword ? (
                          <EyeOff className="h-4 w-4" />
                        ) : (
                          <Eye className="h-4 w-4" />
                        )}
                      </button>
                    </div>
                  </div>

                  {/* Remember Me & Forgot Password */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="remember"
                        checked={rememberMe}
                        onCheckedChange={(checked) => setRememberMe(checked)}
                      />
                      <label
                        htmlFor="remember"
                        className="text-sm text-muted-foreground dark:text-muted-foreground cursor-pointer"
                      >
                        Remember me
                      </label>
                    </div>
                    <Button variant="link" className="px-0 text-sm text-primary dark:text-primary hover:underline" onClick={onForgot}>
                      Forgot password?
                    </Button>
                  </div>

                  {/* Submit Button */}
                  <Button type="submit" className="w-full dark:bg-primary dark:text-primary-foreground dark:hover:bg-primary/90" size="lg">
                    Sign In
                  </Button>
                </form>

                {/* Divider */}
                <div className="relative">
                  <div className="absolute inset-0 flex items-center">
                    <Separator />
                  </div>
                  <div className="relative flex justify-center text-xs uppercase">
                    <span className="bg-card dark:bg-card px-2 text-muted-foreground dark:text-muted-foreground">
                      Or continue with
                    </span>
                  </div>
                </div>

                {/* Social Login */}
                <div className="grid grid-cols-3 gap-3">
                  <Button variant="outline" className="w-full dark:border-border dark:text-foreground dark:hover:bg-accent/50">
                    <Chrome className="h-4 w-4" />
                  </Button>
                  <Button variant="outline" className="w-full dark:border-border dark:text-foreground dark:hover:bg-accent/50">
                    <Github className="h-4 w-4" />
                  </Button>
                  <Button variant="outline" className="w-full dark:border-border dark:text-foreground dark:hover:bg-accent/50">
                    <Linkedin className="h-4 w-4" />
                  </Button>
                </div>

                {/* Sign Up Link */}
                <div className="text-center text-sm">
                  <span className="text-muted-foreground dark:text-muted-foreground">Don't have an account? </span>
                  <Button
                    variant="link"
                    onClick={onSignup}
                    className="px-1 text-primary dark:text-primary hover:underline"
                  >
                    Sign up
                  </Button>
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Right Side - Image & Features */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="hidden lg:block space-y-6"
          >
            <div className="rounded-2xl overflow-hidden shadow-2xl">
              <ImageWithFallback
                src="https://images.unsplash.com/photo-1759668358660-0d06064f0f84?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxtb2Rlcm4lMjB3b3Jrc3BhY2UlMjBsYXB0b3B8ZW58MXx8fHwxNzYwMzY3NzQ2fDA&ixlib=rb-4.0.0&q=80&w=1080&utm_source=figma&utm_medium=referral"
                alt="Modern workspace"
                className="w-full h-auto"
              />
            </div>

            <div className="space-y-4">
              <h3 className="text-2xl text-foreground dark:text-foreground">Continue Your Learning Journey</h3>
              <p className="text-muted-foreground dark:text-muted-foreground text-lg">
                Pick up right where you left off and keep making progress toward your goals.
              </p>
              
              <div className="grid gap-3">
                {[
                  "Access your personalized learning paths",
                  "Track your progress across all courses",
                  "Connect with a community of learners",
                  "Earn certificates and achievements",
                ].map((feature, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.3, delay: 0.4 + index * 0.1 }}
                    className="flex items-center gap-3 p-3 bg-secondary/30 dark:bg-secondary/30 rounded-lg"
                  >
                    <div className="w-6 h-6 rounded-full bg-primary/20 dark:bg-primary/20 flex items-center justify-center flex-shrink-0">
                      <div className="w-2 h-2 rounded-full bg-primary dark:bg-primary" />
                    </div>
                    <span className="text-foreground dark:text-foreground">{feature}</span>
                  </motion.div>
                ))}
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
