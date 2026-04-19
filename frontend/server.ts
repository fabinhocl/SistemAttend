import express from 'express';
import cors from 'cors';
import { createServer as createViteServer } from 'vite';
import path from 'path';
import { fileURLToPath } from 'url';
import Database from 'better-sqlite3';
import Stripe from 'stripe';
import dotenv from 'dotenv';

dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const db = new Database('educontrol.db');

// Initialize Database
db.exec(`
  CREATE TABLE IF NOT EXISTS tenants (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL
  );

  CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id TEXT NOT NULL,
    name TEXT NOT NULL,
    cpf TEXT,
    email TEXT,
    phone TEXT,
    responsible_name TEXT,
    hourly_rate REAL,
    due_day INTEGER,
    notes TEXT,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id)
  );

  CREATE TABLE IF NOT EXISTS packages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id TEXT NOT NULL,
    name TEXT NOT NULL,
    num_classes INTEGER NOT NULL,
    price REAL NOT NULL,
    validity_days INTEGER,
    category TEXT,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id)
  );

  CREATE TABLE IF NOT EXISTS contracts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id TEXT NOT NULL,
    student_id INTEGER NOT NULL,
    package_id INTEGER NOT NULL,
    start_date TEXT NOT NULL,
    preferred_instructor TEXT,
    status TEXT DEFAULT 'active',
    FOREIGN KEY (tenant_id) REFERENCES tenants(id),
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (package_id) REFERENCES packages(id)
  );
`);

// Seed initial data if empty
const tenantCount = db.prepare('SELECT count(*) as count FROM tenants').get() as { count: number };
if (tenantCount.count === 0) {
  db.prepare('INSERT INTO tenants (id, name) VALUES (?, ?)').run('prof_ricardo', 'Prof. Ricardo');
  db.prepare('INSERT INTO students (tenant_id, name, cpf, email) VALUES (?, ?, ?, ?)').run('prof_ricardo', 'João Silva', '123.456.789-00', 'joao@example.com');
  db.prepare('INSERT INTO students (tenant_id, name, cpf, email) VALUES (?, ?, ?, ?)').run('prof_ricardo', 'Maria Oliveira', '987.654.321-11', 'maria@example.com');
  db.prepare('INSERT INTO packages (tenant_id, name, num_classes, price, validity_days, category) VALUES (?, ?, ?, ?, ?, ?)').run('prof_ricardo', 'Pacote 12 Aulas Individuais', 12, 1200.00, 90, 'Premium');
}

async function startServer() {
  const app = express();
  const PORT = 3000;

  app.use(cors());
  app.use(express.json());

  // Middleware for Multi-tenancy
  app.use((req, res, next) => {
    const tenantId = req.headers['x-tenant-id'] as string;
    if (!tenantId && req.path.startsWith('/api')) {
      // For demo purposes, we'll default to 'prof_ricardo' if not provided
      (req as any).tenantId = 'prof_ricardo';
    } else {
      (req as any).tenantId = tenantId;
    }
    next();
  });

  // Stripe Integration
  let stripe: Stripe | null = null;
  if (process.env.STRIPE_SECRET_KEY) {
    stripe = new Stripe(process.env.STRIPE_SECRET_KEY);
  }

  app.post('/api/create-payment-intent', async (req, res) => {
    if (!stripe) {
      return res.status(500).json({ error: 'Stripe not configured' });
    }
    const { amount, payment_method_types } = req.body;
    try {
      const paymentIntent = await stripe.paymentIntents.create({
        amount: Math.round(amount * 100),
        currency: 'brl',
        payment_method_types: payment_method_types || ['card', 'pix'],
      });
      res.json({ clientSecret: paymentIntent.client_secret });
    } catch (e: any) {
      res.status(400).json({ error: e.message });
    }
  });

  // REST API Endpoints
  app.get('/api/students', (req, res) => {
    const tenantId = (req as any).tenantId;
    const students = db.prepare('SELECT * FROM students WHERE tenant_id = ?').all(tenantId);
    res.json(students);
  });

  app.post('/api/students', (req, res) => {
    const tenantId = (req as any).tenantId;
    const { name, cpf, email, phone, responsible_name, hourly_rate, due_day, notes } = req.body;
    const info = db.prepare(`
      INSERT INTO students (tenant_id, name, cpf, email, phone, responsible_name, hourly_rate, due_day, notes)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    `).run(tenantId, name, cpf, email, phone, responsible_name, hourly_rate, due_day, notes);
    res.json({ id: info.lastInsertRowid });
  });

  app.get('/api/packages', (req, res) => {
    const tenantId = (req as any).tenantId;
    const packages = db.prepare('SELECT * FROM packages WHERE tenant_id = ?').all(tenantId);
    res.json(packages);
  });

  app.post('/api/packages', (req, res) => {
    const tenantId = (req as any).tenantId;
    const { name, num_classes, price, validity_days, category } = req.body;
    const info = db.prepare(`
      INSERT INTO packages (tenant_id, name, num_classes, price, validity_days, category)
      VALUES (?, ?, ?, ?, ?, ?)
    `).run(tenantId, name, num_classes, price, validity_days, category);
    res.json({ id: info.lastInsertRowid });
  });

  app.get('/api/contracts', (req, res) => {
    const tenantId = (req as any).tenantId;
    const contracts = db.prepare(`
      SELECT c.*, s.name as student_name, p.name as package_name 
      FROM contracts c
      JOIN students s ON c.student_id = s.id
      JOIN packages p ON c.package_id = p.id
      WHERE c.tenant_id = ?
    `).all(tenantId);
    res.json(contracts);
  });

  app.post('/api/contracts', (req, res) => {
    const tenantId = (req as any).tenantId;
    const { student_id, package_id, start_date, preferred_instructor } = req.body;
    const info = db.prepare(`
      INSERT INTO contracts (tenant_id, student_id, package_id, start_date, preferred_instructor)
      VALUES (?, ?, ?, ?, ?)
    `).run(tenantId, student_id, package_id, start_date, preferred_instructor);
    res.json({ id: info.lastInsertRowid });
  });

  // Vite middleware for development
  if (process.env.NODE_ENV !== 'production') {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: 'spa',
    });
    app.use(vite.middlewares);
  } else {
    app.use(express.static(path.join(__dirname, 'dist')));
    app.get('*', (req, res) => {
      res.sendFile(path.join(__dirname, 'dist', 'index.html'));
    });
  }

  app.listen(PORT, '0.0.0.0', () => {
    console.log(`Server running on http://localhost:${PORT}`);
  });
}

startServer();
