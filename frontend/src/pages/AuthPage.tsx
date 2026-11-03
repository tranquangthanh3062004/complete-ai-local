import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { useAuthStore } from '@/store/authStore';
import { api } from '@/services/api';
import { useToast } from '@/hooks/use-toast';
import { Train, LogIn, UserPlus, Loader2, ArrowRight } from 'lucide-react';

export default function AuthPage() {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  const setAuth = useAuthStore((state) => state.setAuth);
  const navigate = useNavigate();
  const { toast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      toast({
        title: 'Thiếu thông tin',
        description: 'Vui lòng điền đầy đủ email và mật khẩu.',
        variant: 'destructive',
      });
      return;
    }

    setIsLoading(true);
    try {
      if (isLogin) {
        // Form-data request for OAuth2 token
        const formData = new URLSearchParams();
        formData.append('username', email);
        formData.append('password', password);

        const res = await api.post('/auth/token', formData, {
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        });

        const token = res.data.access_token;
        
        // Fetch current user details
        const meRes = await api.get('/auth/me', {
          headers: { Authorization: `Bearer ${token}` }
        });

        setAuth(token, meRes.data);
        toast({
          title: 'Đăng nhập thành công',
          description: `Chào mừng ${meRes.data.display_name || email} quay trở lại!`,
        });
        navigate('/');
      } else {
        // Register request
        await api.post('/auth/register', {
          email,
          password,
          display_name: displayName || email.split('@')[0],
          role: 'user'
        });

        toast({
          title: 'Đăng ký thành công',
          description: 'Tài khoản đã được tạo. Vui lòng đăng nhập.',
        });
        setIsLogin(true);
      }
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Thao tác không thành công. Vui lòng thử lại.';
      toast({
        title: isLogin ? 'Đăng nhập thất bại' : 'Đăng ký thất bại',
        description: typeof msg === 'string' ? msg : JSON.stringify(msg),
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex-1 flex items-center justify-center p-4">
      <Card className="w-full max-w-md shadow-2xl border-border/80 backdrop-blur-md bg-card/95">
        <CardHeader className="text-center space-y-2">
          <div className="mx-auto w-12 h-12 rounded-2xl bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center shadow-lg text-white mb-2">
            <Train size={24} />
          </div>
          <CardTitle className="text-2xl font-bold tracking-tight">
            {isLogin ? 'Đăng nhập COMPLETE AI' : 'Tạo tài khoản mới'}
          </CardTitle>
          <CardDescription>
            {isLogin 
              ? 'Truy cập để lưu lịch sử lộ trình và nhận diện cá nhân hóa' 
              : 'Đăng ký thành viên để trải nghiệm đầy đủ các tính năng thông minh'}
          </CardDescription>
        </CardHeader>

        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4">
            {!isLogin && (
              <div className="space-y-2">
                <Label htmlFor="displayName">Tên hiển thị</Label>
                <Input
                  id="displayName"
                  type="text"
                  placeholder="Nguyễn Văn A"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  disabled={isLoading}
                />
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="email">Địa chỉ Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="name@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={isLoading}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Mật khẩu</Label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={isLoading}
                required
              />
            </div>
          </CardContent>

          <CardFooter className="flex flex-col space-y-3">
            <Button type="submit" className="w-full font-semibold shadow-md" disabled={isLoading}>
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin mr-2" /> Đang xử lý...
                </>
              ) : isLogin ? (
                <>
                  <LogIn className="w-4 h-4 mr-2" /> Đăng nhập
                </>
              ) : (
                <>
                  <UserPlus className="w-4 h-4 mr-2" /> Tạo tài khoản
                </>
              )}
            </Button>

            <button
              type="button"
              onClick={() => setIsLogin(!isLogin)}
              className="text-xs text-muted-foreground hover:text-primary transition-colors flex items-center justify-center gap-1"
            >
              {isLogin ? (
                <>Chưa có tài khoản? <span className="font-semibold text-primary">Đăng ký ngay</span> <ArrowRight size={12} /></>
              ) : (
                <>Đã có tài khoản? <span className="font-semibold text-primary">Đăng nhập</span></>
              )}
            </button>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
