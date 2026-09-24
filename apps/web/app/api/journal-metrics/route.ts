import { NextResponse } from 'next/server';
const API_URL = process.env.API_URL ?? 'http://127.0.0.1:8000';

export async function GET(req: Request) {
  try {
    const { searchParams } = new URL(req.url);
    const res = await fetch(`${API_URL}/api/journal-metrics?${searchParams.toString()}`);
    const data = await res.json();
    return NextResponse.json(data);
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
