import { NextResponse } from 'next/server';
const API_URL = process.env.API_URL ?? 'http://127.0.0.1:8000';

export async function GET() {
  try {
    const res = await fetch(`${API_URL}/api/health`);
    const data = await res.json();
    return NextResponse.json(data);
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
