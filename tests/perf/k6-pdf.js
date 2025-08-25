import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  vus: 30,
  duration: '30s',
};

const yaml = open('../../invoice_portal/static/samples/invoices.yaml');

export default function () {
  const res = http.post('http://127.0.0.1:8000/invoice/1/pdf', { client_data: yaml });
  check(res, { 'status 200': (r) => r.status === 200 });
  sleep(1);
}

