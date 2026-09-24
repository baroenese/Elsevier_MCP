import { NextResponse } from 'next/server';
const API_URL = process.env.API_URL ?? 'http://127.0.0.1:8000';

export async function GET() {
  try {
    const res = await fetch(`${API_URL}/api/config`);
    const data = await res.json();
    return NextResponse.json(data);
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
export async function POST(req: Request) {
  try {
    const body = await req.json();
    const res = await fetch(`${API_URL}/api/config`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    return NextResponse.json(data);
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
