# Build Size Analysis

An investigation was conducted on the workspace directory `New folder (3)` and the related `WP500_TEST_SUITE_v2` directory on the Desktop. The total size of the `WP500_TEST_SUITE_v2` directory is **10.96 GB** (and `New folder (3)` is **3.93 GB**). 

Below is the detailed breakdown of the largest files and duplicate folders causing this footprint.

---

## 1. High-Space-Taking Files & Archives
The following files are the primary space consumers inside the project directory:

| Relative File Path | Size (GB) | Size (MB) | Description |
| :--- | :--- | :--- | :--- |
| `documentation/TAS_WP500_MQAT/WP500_TEST_SUITE_v2.zip` | **2.87 GB** | 2,942.55 MB | A backup zip archive of the entire project directory stored *inside* the project. |
| `.git/objects/pack/pack-52432...303189.pack` | **0.87 GB** | 889.18 MB | Git packfile storing history, bloated from tracking large binaries. |
| `WP500_TEST_SUITE/pages.zip` | **0.84 GB** | 856.41 MB | A backup zip archive of the `pages` directory. |
| `WP500_TEST_SUITE/Backend/web/reference-images/4_firmware_deployment/4.a._FIRMWARE_LOADER/UUU Tool.zip` | **0.77 GB** | 787.06 MB | Compressed archive of the NXP UUU Tool. |
| `WP500_TEST_SUITE/Frontend/dist/client/reference-images/4_firmware_deployment/4.a._FIRMWARE_LOADER/UUU Tool.zip` | **0.77 GB** | 787.06 MB | Duplicate copy of UUU Tool in Frontend distribution folder. |
| `WP500_TEST_SUITE/pages/4_firmware_deployment/4.a._FIRMWARE_LOADER/UUU Tool.zip` | **0.77 GB** | 787.06 MB | Source copy of UUU Tool in `pages`. |
| `WP500_TEST_SUITE/Backend/web/reference-images/4_firmware_deployment/4.a._FIRMWARE_LOADER/uuu/UUU_Tool/taswp500-image-0.6.6-0.rootfs.wic.bz2` | **0.77 GB** | 786.04 MB | Large OS/firmware bz2 image file. |
| `WP500_TEST_SUITE/Frontend/dist/client/reference-images/4_firmware_deployment/4.a._FIRMWARE_LOADER/uuu/UUU_Tool/taswp500-image-0.6.6-0.rootfs.wic.bz2` | **0.77 GB** | 786.04 MB | Duplicate copy of the bz2 firmware image in Frontend distribution folder. |
| `WP500_TEST_SUITE/Backend/qa-api.exe` | **0.18 GB** | 179.45 MB | Compiled Go backend executable. |
| `wp500_qa_suite.exe` | **0.17 GB** | 172.71 MB | Compiled standalone suite executable at the root level. |
| `WP500_TEST_SUITE/pages/4_firmware_deployment/4.a._FIRMWARE_LOADER/uuu/UUU_Tool/taswp500-image-0.6.6-0.rootfs.wic.bz2` | **0.15 GB** | 152.00 MB | Another version of the bz2 firmware image. |
| `WP500_TEST_SUITE/Frontend/node_modules/@cloudflare/workerd-windows-64/bin/workerd.exe` | **0.08 GB** | 85.71 MB | Cloudflare Workerd binary dependency in node modules. |
| `WP500_TEST_SUITE/Backend/bin/node.exe` | **0.07 GB** | 66.77 MB | Node.exe runtime binary. |
| `WP500_TEST_SUITE/Backend/cmd/qa-api/embed/bin/node.exe` | **0.07 GB** | 66.77 MB | Duplicate copy of Node.exe runtime nested for Go embed. |

---

## 2. Duplicate Redundant Files
A major cause of the excessive size is the duplication of massive files across different stages of build/pages:

1. **`UUU Tool.zip` (~787 MB) is duplicated 3 times:**
   - Source: `WP500_TEST_SUITE/pages/4_firmware_deployment/4.a._FIRMWARE_LOADER/UUU Tool.zip`
   - Copied to: `WP500_TEST_SUITE/Backend/web/reference-images/...`
   - Copied to: `WP500_TEST_SUITE/Frontend/dist/client/...`
   - **Total space wasted by duplicates: ~2.36 GB**

2. **`taswp500-image-0.6.6-0.rootfs.wic.bz2` (~786 MB) is duplicated 2.5 times:**
   - Source: `WP500_TEST_SUITE/pages/...` (contains a 152 MB version)
   - Copied to: `WP500_TEST_SUITE/Backend/web/...` (contains a 786 MB version)
   - Copied to: `WP500_TEST_SUITE/Frontend/dist/client/...` (contains a 786 MB version)
   - **Total space wasted by duplicates: ~1.72 GB**

---

## 3. Git Repository Bloat (`.git` Folder)
The Git history (`.git/`) has grown to **1.08 GB**. This is because Git preserves the historical snapshots of every version of the large `.zip` files, executable binaries, and `.wic.bz2` image files that were previously committed or modified. 

Once binaries are tracked in Git, the `.git` directory retains their history even if you delete them from the workspace.

---

## 4. Heavy Toolchain Dependencies
Since you are using Go and React/Vite/Node:
- **`node_modules`** under `Frontend/node_modules/` occupies **411 MB** on disk, including heavy CLI runtimes like `@cloudflare/workerd-windows-64/bin/workerd.exe` (**85.71 MB**).
- **`node.exe`** is copied multiple times (e.g., in `Backend/bin` and `Backend/cmd/qa-api/embed/bin`) to allow self-contained embedding in the Go executable, adding **133.5 MB** of static binaries.

---

## 5. Other Large Files on Desktop (Outside Workspace)
If you check the overall disk space usage on the Desktop, there are several large archives of this project:
* `WP500_TEST_SUITE_v2 (3).zip` — **15.44 GB**
* `WP500_TEST_SUITE_v2 (2).zip` — **10.45 GB**
* `WP500_TEST_SUITE_v2.zip` — **6.48 GB**
* `zips/` directory — **13.45 GB**
* `store/` directory — **6.30 GB**

---

## Summary of Recommendations (No changes were made)
To bring the build back down below **0.5 GB / 500 MB**, you can:
1. **Exclude large archives/zips**: Move/delete `documentation/TAS_WP500_MQAT/WP500_TEST_SUITE_v2.zip` (2.87 GB) and `WP500_TEST_SUITE/pages.zip` (0.84 GB) out of the project folder.
2. **Move large firmware assets out of the build path**: `UUU Tool.zip` (787 MB) and `taswp500-image-...wic.bz2` (786 MB) do not need to be packaged inside the web app's static assets. Moving them to an external folder (or downloading them dynamically) will save **~4 GB** of space.
3. **Configure Go Embed to exclude binaries/caches**: Ensure that Go does not embed the parent directories of caches or large files.
4. **Purge Git History**: Run `git-filter-repo` or BFG Repo-Cleaner to completely remove the heavy binaries from the Git repository history.
