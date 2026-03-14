// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

contract DocumentVerification {
    struct VerificationRecord {
        string applicantId;
        bytes32[] docHashes;
        uint8 confidence;
        bool isVerified;
        uint256 timestamp;
    }

    mapping(string => VerificationRecord[]) private records;

    event VerificationStored(
        string applicantId,
        uint8 confidence,
        bool isVerified,
        uint256 timestamp
    );

    function storeVerification(
        string memory applicantId,
        bytes32[] memory docHashes,
        uint8 confidence,
        bool isVerified
    ) external {
        records[applicantId].push(VerificationRecord({
            applicantId: applicantId,
            docHashes: docHashes,
            confidence: confidence,
            isVerified: isVerified,
            timestamp: block.timestamp
        }));
        emit VerificationStored(applicantId, confidence, isVerified, block.timestamp);
    }

    function getRecords(string memory applicantId)
        external
        view
        returns (VerificationRecord[] memory)
    {
        return records[applicantId];
    }
}
