process.env.NODE_ENV = 'production';

const { createServer } = require('http');
const next = require('next');

const port = Number.parseInt(process.env.PORT || '3000', 10);
const hostname = process.env.HOSTNAME || '0.0.0.0';

// Always boot the production server so the app serves the hashed build assets.
const app = next({ dev: false, hostname, port });
const handle = app.getRequestHandler();

app.prepare().then(() => {
  createServer((req, res) => {
    handle(req, res);
  }).listen(port, hostname, () => {
    // eslint-disable-next-line no-console
    console.log(`Ready on http://${hostname}:${port}`);
  });
});
