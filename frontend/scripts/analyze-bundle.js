/**
 * Bundle Analyzer Script
 *
 * Analyzes the production bundle size and generates reports
 * to help identify large dependencies and optimization opportunities.
 */

import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'fs';
import { join } from 'path';
import { fileURLToPath } from 'url';
import { gzipSync, brotliCompressSync } from 'zlib';
import { parse } from 'acorn';
import { simple } from 'acorn-walk';

const __filename = fileURLToPath(import.meta.url);
const __dirname = join(__filename, '..');

/**
 * Analyze bundle size
 */
function analyzeBundle(bundlePath) {
  console.log('📦 Analyzing bundle:', bundlePath);

  if (!existsSync(bundlePath)) {
    console.error('❌ Bundle file not found:', bundlePath);
    process.exit(1);
  }

  const bundleCode = readFileSync(bundlePath, 'utf-8');
  const bundleSize = Buffer.byteLength(bundleCode, 'utf-8');
  const gzipSize = Buffer.byteLength(gzipSync(bundleCode), 'utf-8');
  const brotliSize = Buffer.byteLength(brotliCompressSync(bundleCode), 'utf-8');

  console.log('\n📊 Bundle Size Report');
  console.log('─'.repeat(50));
  console.log(`Bundle Size: ${(bundleSize / 1024).toFixed(2)} KB`);
  console.log(`Gzip Size: ${(gzipSize / 1024).toFixed(2)} KB`);
  console.log(`Brotli Size: ${(brotliSize / 1024).toFixed(2)} KB`);

  return {
    bundleSize,
    gzipSize,
    brotliSize,
  };
}

/**
 * Extract dependencies from bundle
 */
function extractDependencies(bundleCode) {
  const dependencies = new Map();

  try {
    const ast = parse(bundleCode, {
      ecmaVersion: 'latest',
      sourceType: 'module',
    });

    simple(ast, {
      ImportDeclaration(node) {
        if (node.source && node.source.value) {
          const dep = node.source.value;
          if (!dependencies.has(dep)) {
            dependencies.set(dep, 0);
          }
          dependencies.set(dep, dependencies.get(dep) + 1);
        }
      },
      CallExpression(node) {
        if (
          node.callee.type === 'Identifier' &&
          node.callee.name === 'require' &&
          node.arguments.length > 0 &&
          node.arguments[0].type === 'Literal'
        ) {
          const dep = node.arguments[0].value;
          if (typeof dep === 'string' && !dependencies.has(dep)) {
            dependencies.set(dep, 0);
          }
          dependencies.set(dep, (dependencies.get(dep) || 0) + 1);
        }
      },
    });
  } catch (error) {
    console.warn('⚠️ Could not parse bundle for dependencies:', error.message);
  }

  return Array.from(dependencies.entries())
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count);
}

/**
 * Generate HTML report
 */
function generateHTMLReport(stats, outputPath) {
  const html = `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Bundle Analysis Report</title>
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
      max-width: 1200px;
      margin: 0 auto;
      padding: 20px;
      background: #f9fafb;
    }
    .header {
      background: white;
      padding: 30px;
      border-radius: 8px;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
      margin-bottom: 20px;
    }
    .metrics {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 20px;
      margin-bottom: 30px;
    }
    .metric-card {
      background: white;
      padding: 20px;
      border-radius: 8px;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }
    .metric-value {
      font-size: 32px;
      font-weight: bold;
      color: #2563eb;
      margin: 10px 0;
    }
    .metric-label {
      font-size: 14px;
      color: #6b7280;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .dependencies {
      background: white;
      padding: 30px;
      border-radius: 8px;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 20px;
    }
    th, td {
      padding: 12px;
      text-align: left;
      border-bottom: 1px solid #e5e7eb;
    }
    th {
      background: #f9fafb;
      font-weight: 600;
      color: #374151;
    }
    tr:hover {
      background: #f9fafb;
    }
    .recommendation {
      background: #eff6ff;
      border-left: 4px solid #2563eb;
      padding: 15px;
      margin: 20px 0;
      border-radius: 4px;
    }
    .warning {
      background: #fef3c7;
      border-left: 4px solid #f59e0b;
      padding: 15px;
      margin: 20px 0;
      border-radius: 4px;
    }
    h1 {
      color: #111827;
      margin: 0;
    }
    h2 {
      color: #374151;
      margin-top: 30px;
    }
    code {
      background: #f3f4f6;
      padding: 2px 6px;
      border-radius: 3px;
      font-size: 0.9em;
    }
  </style>
</head>
<body>
  <div class="header">
    <h1>📦 Bundle Analysis Report</h1>
    <p style="color: #6b7280; margin-top: 10px;">Generated on ${new Date().toLocaleString()}</p>
  </div>

  <div class="metrics">
    <div class="metric-card">
      <div class="metric-label">Total Bundle Size</div>
      <div class="metric-value">${(stats.bundleSize / 1024).toFixed(2)} KB</div>
    </div>
    <div class="metric-card">
      <div class="metric-label">Gzip Size</div>
      <div class="metric-value">${(stats.gzipSize / 1024).toFixed(2)} KB</div>
    </div>
    <div class="metric-card">
      <div class="metric-label">Brotli Size</div>
      <div class="metric-value">${(stats.brotliSize / 1024).toFixed(2)} KB</div>
    </div>
  </div>

  ${generateRecommendations(stats)}

  <div class="dependencies">
    <h2>Top Dependencies</h2>
    <table>
      <thead>
        <tr>
          <th>Dependency</th>
          <th>Usage Count</th>
        </tr>
      </thead>
      <tbody>
        ${stats.dependencies
          .map(
            (dep) => `
          <tr>
            <td><code>${dep.name}</code></td>
            <td>${dep.count}</td>
          </tr>
        `
          )
          .join('')}
      </tbody>
    </table>
  </div>
</body>
</html>
  `;

  writeFileSync(outputPath, html);
  console.log('📄 HTML report generated:', outputPath);
}

/**
 * Generate recommendations based on bundle size
 */
function generateRecommendations(stats) {
  const recommendations = [];

  if (stats.gzipSize > 500 * 1024) {
    recommendations.push({
      type: 'warning',
      text: `Bundle size is ${(stats.gzipSize / 1024).toFixed(2)} KB (Gzip). Consider implementing code splitting and removing unused dependencies.`,
    });
  }

  if (stats.gzipSize > 250 * 1024) {
    recommendations.push({
      type: 'recommendation',
      text: 'Bundle size is approaching the recommended limit. Review dependencies and consider lazy loading heavy components.',
    });
  }

  if (stats.brotliSize < stats.gzipSize * 0.7) {
    recommendations.push({
      type: 'recommendation',
      text: 'Good compression ratio detected. Ensure Brotli compression is enabled in production.',
    });
  }

  if (recommendations.length === 0) {
    return '<div class="recommendation">✅ Bundle size is within acceptable limits!</div>';
  }

  return recommendations
    .map((rec) => {
      const className = rec.type === 'warning' ? 'warning' : 'recommendation';
      return `<div class="${className}">${rec.text}</div>`;
    })
    .join('');
}

/**
 * Main function
 */
function main() {
  const bundlePath = join(process.cwd(), 'dist', 'assets', 'index-*.js');
  const outputPath = join(process.cwd(), 'dist', 'bundle-report.html');

  console.log('🚀 Starting bundle analysis...\n');

  // For now, we'll just analyze the stats.html from rollup-plugin-visualizer
  const statsPath = join(process.cwd(), 'dist', 'stats.html');

  if (existsSync(statsPath)) {
    console.log('📊 Using stats from rollup-plugin-visualizer...');
    console.log('Open dist/stats.html to view the interactive bundle analyzer.');
  }

  // Analyze bundle if it exists
  const jsFiles = existsSync(join(process.cwd(), 'dist', 'assets'))
    ? require('fs').readdirSync(join(process.cwd(), 'dist', 'assets')).filter(f => f.endsWith('.js'))
    : [];

  if (jsFiles.length > 0) {
    const bundlePath = join(process.cwd(), 'dist', 'assets', jsFiles[0]);
    const stats = analyzeBundle(bundlePath);

    console.log('\n📦 Extracting dependencies...');
    const bundleCode = readFileSync(bundlePath, 'utf-8');
    const dependencies = extractDependencies(bundleCode);

    console.log('\nTop 10 Dependencies:');
    dependencies.slice(0, 10).forEach((dep) => {
      console.log(`  ${dep.name}: ${dep.count} imports`);
    });

    const reportStats = {
      ...stats,
      dependencies,
    };

    console.log('\n📄 Generating HTML report...');
    generateHTMLReport(reportStats, outputPath);
  }

  console.log('\n✅ Bundle analysis complete!');
  console.log('\n💡 Tips:');
  console.log('  - Keep bundle size under 500KB (Gzip)');
  console.log('  - Use code splitting for large libraries');
  console.log('  - Remove unused dependencies');
  console.log('  - Enable Brotli compression in production');
}

main();
