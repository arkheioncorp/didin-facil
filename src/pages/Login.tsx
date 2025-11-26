import * as React from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { TikTrendIcon, EyeIcon, EyeOffIcon } from "@/components/icons";
import { useUserStore } from "@/stores";
import { useNavigate, useLocation } from "react-router-dom";

export const Login: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { setUser, setLicense } = useUserStore();
  const [isLoading, setIsLoading] = React.useState(false);
  const [isRegister, setIsRegister] = React.useState(location.pathname === "/register");
  
  React.useEffect(() => {
    setIsRegister(location.pathname === "/register");
  }, [location.pathname]);

  const [formData, setFormData] = React.useState({
    email: "",
    password: "",
    name: "",
    confirmPassword: "",
  });
  const [errors, setErrors] = React.useState<Record<string, string>>({});
  const [showPassword, setShowPassword] = React.useState(false);

  const validateForm = () => {
    const newErrors: Record<string, string> = {};
    if (!formData.email) {
      newErrors.email = "E-mail é obrigatório";
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = "E-mail inválido";
    }

    if (!formData.password) {
      newErrors.password = "Senha é obrigatória";
    } else if (isRegister && formData.password.length < 8) {
      newErrors.password = "A senha deve ter pelo menos 8 caracteres";
    }

    if (isRegister) {
      if (!formData.name) newErrors.name = "Nome é obrigatório";
      if (formData.password !== formData.confirmPassword) {
        newErrors.confirmPassword = "As senhas não coincidem";
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;
    
    setIsLoading(true);
    setErrors({});

    // Simulating login/register
    setTimeout(() => {
      if (formData.email === "wrong@example.com") {
         setErrors({ root: "Credenciais incorretas" });
         setIsLoading(false);
         return;
      }

      // Mock user data
      const mockUser = {
        id: "user_" + Date.now(),
        email: formData.email,
        name: formData.name || formData.email.split("@")[0],
        plan: "trial" as const,
        planExpiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
        createdAt: new Date().toISOString(),
      };

      const mockLicense = {
        isValid: true,
        plan: "trial" as const,
        features: {
          searchesPerMonth: 10,
          copiesPerMonth: 5,
          favoriteLists: 1,
          exportEnabled: false,
          schedulerEnabled: false,
        },
        expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
        usageThisMonth: {
          searches: 0,
          copies: 0,
        },
      };

      setUser(mockUser);
      setLicense(mockLicense);
      setIsLoading(false);
      navigate("/");
    }, 1500);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background via-background to-tiktrend-primary/5 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center space-y-4">
          <div className="mx-auto flex items-center justify-center gap-2">
            <TikTrendIcon size={48} />
            <span className="text-2xl font-bold bg-gradient-to-r from-tiktrend-primary to-tiktrend-secondary bg-clip-text text-transparent">
              TikTrend Finder
            </span>
          </div>
          <div>
            <CardTitle className="text-xl">
              {isRegister ? "Criar Conta" : "Bem-vindo de Volta"}
            </CardTitle>
            <CardDescription>
              {isRegister
                ? "Crie sua conta para começar a encontrar produtos em alta"
                : "Entre para continuar encontrando produtos virais"}
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent>
          {errors.root && (
            <div
              className="mb-4 p-3 rounded-md bg-destructive/10 text-destructive text-sm"
              data-testid="error-alert"
              role="alert"
            >
              {errors.root}
            </div>
          )}
          <form onSubmit={handleSubmit} className="space-y-4" noValidate>
            {isRegister && (
              <div className="space-y-2">
                <Label htmlFor="name">Nome</Label>
                <Input
                  id="name"
                  placeholder="Seu nome"
                  value={formData.name}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                    setFormData({ ...formData, name: e.target.value })
                  }
                />
                {errors.name && (
                  <p className="text-sm text-destructive">{errors.name}</p>
                )}
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="email">E-mail</Label>
              <Input
                id="email"
                data-testid="email-input"
                type="email"
                placeholder="seu@email.com"
                value={formData.email}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setFormData({ ...formData, email: e.target.value })
                }
              />
              {errors.email && (
                <p className="text-sm text-destructive" data-testid="email-error">
                  {errors.email}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Senha</Label>
              <div className="relative">
                <Input
                  id="password"
                  data-testid="password-input"
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
                  value={formData.password}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                    setFormData({ ...formData, password: e.target.value })
                  }
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                  onClick={() => setShowPassword(!showPassword)}
                  data-testid="password-toggle"
                >
                  {showPassword ? (
                    <EyeOffIcon className="h-4 w-4 text-muted-foreground" />
                  ) : (
                    <EyeIcon className="h-4 w-4 text-muted-foreground" />
                  )}
                </Button>
              </div>
              {errors.password && (
                <p className="text-sm text-destructive" data-testid="password-error">
                  {errors.password}
                </p>
              )}
            </div>

            {isRegister && (
              <div className="space-y-2">
                <Label htmlFor="confirmPassword">Confirmar Senha</Label>
                <Input
                  id="confirmPassword"
                  type="password"
                  placeholder="••••••••"
                  value={formData.confirmPassword}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                    setFormData({ ...formData, confirmPassword: e.target.value })
                  }
                />
                {errors.confirmPassword && (
                  <p className="text-sm text-destructive">{errors.confirmPassword}</p>
                )}
              </div>
            )}

            <Button
              type="submit"
              data-testid="login-button"
              variant="tiktrend"
              className="w-full"
              disabled={isLoading}
            >
              {isLoading ? (
                <span className="flex items-center gap-2">
                  <svg
                    className="animate-spin h-4 w-4"
                    viewBox="0 0 24 24"
                    data-testid="loading-spinner"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                      fill="none"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  Processando...
                </span>
              ) : isRegister ? (
                "Criar Conta"
              ) : (
                "Entrar"
              )}
            </Button>
          </form>

          <div className="mt-6">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <Separator />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-background px-2 text-muted-foreground">
                  ou
                </span>
              </div>
            </div>

            <div className="mt-6 text-center">
              <button
                type="button"
                data-testid="register-link"
                onClick={() => navigate(isRegister ? "/login" : "/register")}
                className="text-sm text-tiktrend-primary hover:text-tiktrend-primary/80 transition-colors"
              >
                {isRegister
                  ? "Já tem uma conta? Entre aqui"
                  : "Não tem conta? Cadastre-se"}
              </button>
            </div>
          </div>

          {/* Trial info */}
          <div className="mt-6 p-4 rounded-lg bg-gradient-to-r from-tiktrend-primary/10 to-tiktrend-secondary/10 text-center">
            <p className="text-sm text-muted-foreground">
              🎁 <strong>7 dias grátis</strong> para testar todas as funcionalidades
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
