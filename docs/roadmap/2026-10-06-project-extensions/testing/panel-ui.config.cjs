const path = require('node:path');
const root = path.resolve(__dirname, '../../../..');
module.exports = {
  testDir: __dirname, testMatch: 'panel-ui.spec.cjs', workers: 1, retries: 0,
  outputDir: path.join(root, 'scratchpad/.venv/panel-preview/extensions-artifacts'),
  reporter: [['json', { outputFile: path.join(root, 'scratchpad/.venv/panel-preview/extensions-results.json') }]],
  use: {
    launchOptions: { executablePath: process.env.EDGE_PATH || 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe' },
    viewport: { width: 1440, height: 1000 },
  },
};
