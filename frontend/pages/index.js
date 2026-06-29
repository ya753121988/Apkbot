import Link from 'next/link';
export default function Home() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-blue-600 text-white">
      <h1 className="text-5xl font-bold">Web to APK SaaS</h1>
      <p className="mt-4 text-xl">Convert any URL to Android, iOS, and PC app in minutes!</p>
      <div className="mt-8 space-x-4">
        <Link href="/signup"><button className="bg-white text-blue-600 px-6 py-2 rounded-lg font-bold">Get Started</button></Link>
        <Link href="/login"><button className="border-2 border-white px-6 py-2 rounded-lg font-bold">Login</button></Link>
      </div>
    </div>
  )
}
