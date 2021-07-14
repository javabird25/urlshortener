import * as path from 'path';
import * as webpack from 'webpack';
import HtmlWebpackPlugin = require('html-webpack-plugin');
import 'webpack-dev-server';

const distPath = path.resolve(__dirname, 'dist');

const config: webpack.Configuration = {
  entry: './src/index.tsx',
  mode: 'production',
  module: {
    rules: [
      {
        test: /\.tsx?$/,
        use: 'ts-loader',
        exclude: /node_modules/,
      },
    ],
  },
  resolve: {
    extensions: ['.tsx', '.ts', '.js'],
  },
  plugins: [
      new HtmlWebpackPlugin({
        title: 'URLShortener',
      }),
  ],
  output: {
    filename: 'bundle.js',
    path: distPath,
  },
};

export default config;
