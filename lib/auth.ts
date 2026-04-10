import type { NextAuthOptions } from "next-auth"
import CredentialsProvider from "next-auth/providers/credentials"
import bcrypt from "bcryptjs"

export const authOptions: NextAuthOptions = {
  providers: [
    CredentialsProvider({
      id: "credentials",
      name: "Credentials",
      credentials: {
        password: { label: "Senha", type: "password" },
      },
      async authorize(credentials) {
        const plain = credentials?.password
        const hash = process.env.ADMIN_PASSWORD
        if (!plain || !hash) {
          return null
        }
        const ok = await bcrypt.compare(plain, hash)
        if (!ok) {
          return null
        }
        return { id: "1", name: "Admin", role: "admin" }
      },
    }),
  ],
  session: { strategy: "jwt", maxAge: 60 * 60 * 12 },
  secret: process.env.NEXTAUTH_SECRET,
  pages: { signIn: "/login" },
  callbacks: {
    async jwt({ token, user }) {
      if (user && "role" in user) {
        token.role = (user as { role?: string }).role
      }
      return token
    },
    async session({ session, token }) {
      if (session.user) {
        session.user.id = token.sub
        session.user.role = token.role as string | undefined
      }
      return session
    },
  },
}
