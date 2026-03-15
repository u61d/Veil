"use strict";

function registerProfile(profilePath) {
  let file = Cc["@mozilla.org/file/local;1"].createInstance(Ci.nsIFile);
  file.initWithPath(profilePath);

  let provider = {
    getFile(prop, persistent) {
      persistent.value = true;
      if (
        prop == "ProfD" ||
        prop == "ProfLD" ||
        prop == "ProfDS" ||
        prop == "ProfLDS" ||
        prop == "TmpD"
      ) {
        return file.clone();
      }
      return null;
    },
    QueryInterface: ChromeUtils.generateQI(["nsIDirectoryServiceProvider"]),
  };

  Services.dirsvc
    .QueryInterface(Ci.nsIDirectoryService)
    .registerProvider(provider);
  try {
    Services.dirsvc.undefine("TmpD");
  } catch (error) {
    if (error.result != Cr.NS_ERROR_FAILURE) {
      throw error;
    }
  }

  Services.obs.notifyObservers(file, "profile-do-change", "xpcshell");
  Services.obs.notifyObservers(file, "profile-after-change", "xpcshell");
}

registerProfile(Services.env.get("XPCSHELL_TEST_PROFILE_DIR"));

ChromeUtils.defineESModuleGetters(this, {
  PushDB: "resource://gre/modules/PushDB.sys.mjs",
  PushRecord: "resource://gre/modules/PushRecord.sys.mjs",
  pushBroadcastService: "resource://gre/modules/PushBroadcastService.sys.mjs",
});

const mode = Services.env.get("VEIL_PUSH_PROFILE_MODE") || "subscription";
const userAgentID = Services.env.get("VEIL_PUSH_USER_AGENT_ID");

const PUSH_DB_NAME = "pushapi";
const PUSH_DB_VERSION = 5;
const PUSH_DB_STORE_NAME = "pushapi";

async function seedSubscriptionRecord() {
  let db = new PushDB(
    PUSH_DB_NAME,
    PUSH_DB_VERSION,
    PUSH_DB_STORE_NAME,
    "channelID",
    PushRecord
  );
  try {
    await db.put({
      channelID: "0ef2ad4a-6c49-41ad-af6e-95d2425276bf",
      pushEndpoint: "https://example.org/push/0ef2ad4a-6c49-41ad-af6e-95d2425276bf",
      scope: "https://example.com/push/subscribed",
      originAttributes: "",
      version: 1,
      pushCount: 1,
      lastPush: Date.now(),
      quota: 16,
    });
  } finally {
    db.close();
  }
}

async function seedBroadcastListener() {
  await pushBroadcastService.initializePromise;
  pushBroadcastService.jsonFile.data.listeners = {
    "veil-broadcast-test": {
      version: "2026-03-14",
      sourceInfo: {
        moduleURI: "resource://gre/modules/PushBroadcastService.sys.mjs",
        symbolName: "pushBroadcastService",
      },
    },
  };
  await pushBroadcastService._saveImmediately();
}

async function main() {
  if (userAgentID) {
    Services.prefs.setStringPref("dom.push.userAgentID", userAgentID);
  }

  if (mode == "subscription" || mode == "both") {
    await seedSubscriptionRecord();
  }
  if (mode == "broadcast" || mode == "both") {
    await seedBroadcastListener();
  }

  print(
    JSON.stringify({
      profileDir: PathUtils.profileDir,
      mode,
      uaidSeeded: !!userAgentID,
    })
  );
}

let done = false;
let exitCode = 0;

main().then(
  () => {
    done = true;
  },
  error => {
    console.error(error);
    exitCode = 1;
    done = true;
  }
);

Services.tm.spinEventLoopUntil("VeilSeedPushProfile", () => done);
quit(exitCode);
