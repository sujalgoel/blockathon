const hre = require("hardhat");

async function main() {
  const DocVerify = await hre.ethers.getContractFactory("DocumentVerification");
  const contract = await DocVerify.deploy();
  await contract.waitForDeployment();
  const address = await contract.getAddress();
  console.log(`DocumentVerification deployed to: ${address}`);
  console.log(`\nAdd to .env:\nCONTRACT_ADDRESS=${address}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
