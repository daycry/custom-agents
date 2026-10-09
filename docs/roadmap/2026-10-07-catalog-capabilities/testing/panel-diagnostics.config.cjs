module.exports={
 testDir:__dirname,testMatch:['panel-hooks.spec.cjs','panel-diagnostics.spec.cjs'],workers:1,retries:0,
 reporter:[['json',{outputFile:process.env.PANEL_RESULTS}]],
 use:{launchOptions:{executablePath:process.env.PANEL_BROWSER},viewport:{width:1440,height:1000}},
};
