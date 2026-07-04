// CRA's webpack 5 enforces "fullySpecified" resolution for ESM modules, which
// breaks Excalidraw's bundle (it imports e.g. `roughjs/bin/rough` without a file
// extension). Relax that rule for .mjs/.js so those bare imports resolve.
module.exports = {
  webpack: {
    configure: (webpackConfig) => {
      webpackConfig.module.rules.push({
        test: /\.m?js$/,
        resolve: { fullySpecified: false },
      });
      return webpackConfig;
    },
  },
};
