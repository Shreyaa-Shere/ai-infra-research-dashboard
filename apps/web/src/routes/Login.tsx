import LoginForm from '../components/LoginForm'

export default function Login() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="w-full max-w-md">
        <h1 className="text-2xl font-bold text-center mb-8 text-gray-900">
          AI Infra Research Dashboard
        </h1>
        <LoginForm />
      </div>
    </div>
  )
}
