const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("DocumentVerification", function () {
  let contract;

  beforeEach(async () => {
    const DocVerify = await ethers.getContractFactory("DocumentVerification");
    contract = await DocVerify.deploy();
  });

  it("stores and retrieves a verification record", async () => {
    const applicantId = "UK-2024-00183";
    const docHash = ethers.keccak256(ethers.toUtf8Bytes("test-doc"));

    await contract.storeVerification(applicantId, [docHash], 91, true);

    const records = await contract.getRecords(applicantId);
    expect(records.length).to.equal(1);
    expect(records[0].applicantId).to.equal(applicantId);
    expect(records[0].confidence).to.equal(91);
    expect(records[0].isVerified).to.equal(true);
  });

  it("returns empty array for unknown applicant", async () => {
    const records = await contract.getRecords("UNKNOWN-ID");
    expect(records.length).to.equal(0);
  });

  it("stores multiple records for the same applicant", async () => {
    const id = "UK-2024-00183";
    const h1 = ethers.keccak256(ethers.toUtf8Bytes("doc1"));
    const h2 = ethers.keccak256(ethers.toUtf8Bytes("doc2"));

    await contract.storeVerification(id, [h1], 80, true);
    await contract.storeVerification(id, [h2], 60, false);

    const records = await contract.getRecords(id);
    expect(records.length).to.equal(2);
    expect(records[0].isVerified).to.equal(true);
    expect(records[1].isVerified).to.equal(false);
  });

  it("emits VerificationStored event", async () => {
    const { anyValue } = require("@nomicfoundation/hardhat-chai-matchers/withArgs");
    const id = "UK-2024-00183";
    const hash = ethers.keccak256(ethers.toUtf8Bytes("doc"));

    await expect(contract.storeVerification(id, [hash], 75, true))
      .to.emit(contract, "VerificationStored")
      .withArgs(id, 75, true, anyValue);
  });
});
