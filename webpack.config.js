const path = require("path");
const webpack = require("webpack");
const { CleanWebpackPlugin } = require("clean-webpack-plugin");
const CopyWebpackPlugin = require("copy-webpack-plugin");
const CompressionPlugin = require("compression-webpack-plugin");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const RemoveEmptyScriptsPlugin = require("webpack-remove-empty-scripts");

const mode = process.env.NODE_ENV === "production" ? "production" : "development";
const isProd = mode === "production";

module.exports = {
  mode,
  target: "web",
  entry: {
    main: path.resolve(__dirname, "js", "main-entry.js"),
    style: [
      path.resolve(__dirname, "css", "plugins.css"),
      path.resolve(__dirname, "scss", "style.scss"),
    ],
    rtlStyles: path.resolve(__dirname, "scss", "rtl.scss"),
    rtl: path.resolve(__dirname, "js", "rtl.js"),
  },
  output: {
    filename: (pathData) => (pathData.chunk.name === "rtl" ? "js/rtl.js" : "js/[name].js"),
    path: path.resolve(__dirname, "dist"),
    clean: false,
  },
  resolve: {
    alias: {
      jquery: path.resolve(__dirname, "js", "jquery-3.7.1.min.js"),
    },
  },
  module: {
    rules: [
      {
        test: /\.s?css$/i,
        use: [
          MiniCssExtractPlugin.loader,
          {
            loader: "css-loader",
            options: {
              importLoaders: 1,
              sourceMap: !isProd,
              url: false,
            },
          },
          {
            loader: "sass-loader",
            options: {
              sourceMap: !isProd,
            },
          },
        ],
      },
    ],
  },
  plugins: [
    new CleanWebpackPlugin(),
    new RemoveEmptyScriptsPlugin(),
    new MiniCssExtractPlugin({
      filename: (pathData) =>
        pathData.chunk && pathData.chunk.name === "rtlStyles"
          ? "css/rtl.css"
          : "css/[name].css",
    }),
    new webpack.ProvidePlugin({
      $: "jquery",
      jQuery: "jquery",
      "window.jQuery": "jquery",
    }),
    new CopyWebpackPlugin({
      patterns: [
        {
          from: "*.html",
          to: "[name][ext]",
          context: path.resolve(__dirname),
        },
        { from: "fonts", to: "fonts" },
        { from: "img", to: "img" },
      ],
    }),
    new CompressionPlugin({
      algorithm: "gzip",
      test: /\.(js|css)$/i,
      threshold: 10240,
      minRatio: 0.8,
    }),
  ],
  optimization: {
    splitChunks: false,
  },
  performance: {
    hints: false,
  },
  stats: "errors-warnings",
};
