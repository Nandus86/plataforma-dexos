const fs = require('fs');

const targetPath = './src/environments/environment.prod.ts';
const envConfigFile = `export const environment = {
    production: true,
    apiUrl: '${process.env.API_URL || '/api'}',
    appName: 'Exousía School',
    appSubtitle: 'by Dexos',
};
`;

console.log('Generating environment.prod.ts with API_URL: ' + process.env.API_URL);

fs.writeFile(targetPath, envConfigFile, function (err) {
    if (err) {
        throw console.error(err);
    } else {
        console.log(`Angular environment.prod.ts generated correctly at ${targetPath} \n`);
    }
});
