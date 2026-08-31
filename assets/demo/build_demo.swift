import AVFoundation
import CoreGraphics
import Foundation
import ImageIO

let root = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
let demo = root.appendingPathComponent("assets/demo")
let silentURL = demo.appendingPathComponent("offsite-captain-demo-silent.mov")
let outputURL = demo.appendingPathComponent("offsite-captain-demo.mp4")
let audioURL = demo.appendingPathComponent("offsite-captain-narration.mp3")

let slides: [(String, Double)] = [
    ("01-brief.png", 10.0),
    ("02-conflicts.png", 15.0),
    ("03-plan-review.png", 20.0),
    ("04-validation.png", 20.0),
    ("05-authorized.png", 15.0),
    ("06-confirmed.png", 11.0),
]

for url in [silentURL, outputURL] {
    try? FileManager.default.removeItem(at: url)
}

let width = 1280
let height = 720
let fps: Int32 = 30
let writer = try AVAssetWriter(outputURL: silentURL, fileType: .mov)
let videoSettings: [String: Any] = [
    AVVideoCodecKey: AVVideoCodecType.jpeg,
    AVVideoWidthKey: width,
    AVVideoHeightKey: height,
    AVVideoCompressionPropertiesKey: [
        AVVideoQualityKey: 0.86,
    ],
]
let input = AVAssetWriterInput(mediaType: .video, outputSettings: videoSettings)
input.expectsMediaDataInRealTime = false
let attributes: [String: Any] = [
    kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32BGRA,
    kCVPixelBufferWidthKey as String: width,
    kCVPixelBufferHeightKey as String: height,
]
let adapter = AVAssetWriterInputPixelBufferAdaptor(
    assetWriterInput: input,
    sourcePixelBufferAttributes: attributes
)
guard writer.canAdd(input) else { fatalError("Cannot add video input") }
writer.add(input)
writer.startWriting()
writer.startSession(atSourceTime: .zero)

func image(named name: String) -> CGImage {
    let url = demo.appendingPathComponent(name) as CFURL
    guard let source = CGImageSourceCreateWithURL(url, nil),
          let image = CGImageSourceCreateImageAtIndex(source, 0, nil) else {
        fatalError("Cannot load \(name)")
    }
    return image
}

func pixelBuffer(for image: CGImage) -> CVPixelBuffer {
    var buffer: CVPixelBuffer?
    let status = CVPixelBufferCreate(
        kCFAllocatorDefault, width, height,
        kCVPixelFormatType_32BGRA,
        attributes as CFDictionary,
        &buffer
    )
    guard status == kCVReturnSuccess, let buffer else {
        fatalError("Cannot create pixel buffer")
    }
    CVPixelBufferLockBaseAddress(buffer, [])
    defer { CVPixelBufferUnlockBaseAddress(buffer, []) }
    guard let context = CGContext(
        data: CVPixelBufferGetBaseAddress(buffer),
        width: width,
        height: height,
        bitsPerComponent: 8,
        bytesPerRow: CVPixelBufferGetBytesPerRow(buffer),
        space: CGColorSpaceCreateDeviceRGB(),
        bitmapInfo: CGBitmapInfo.byteOrder32Little.rawValue |
            CGImageAlphaInfo.premultipliedFirst.rawValue
    ) else { fatalError("Cannot create drawing context") }
    context.setFillColor(CGColor(red: 0.98, green: 0.97, blue: 0.94, alpha: 1))
    context.fill(CGRect(x: 0, y: 0, width: width, height: height))
    context.interpolationQuality = .high
    context.draw(image, in: CGRect(x: 0, y: 0, width: width, height: height))
    return buffer
}

var frame: Int64 = 0
for (name, duration) in slides {
    let buffer = pixelBuffer(for: image(named: name))
    let frameCount = Int64((duration * Double(fps)).rounded())
    for _ in 0..<frameCount {
        while !input.isReadyForMoreMediaData { usleep(2_000) }
        let time = CMTime(value: frame, timescale: fps)
        guard adapter.append(buffer, withPresentationTime: time) else {
            fatalError("Video append failed: \(writer.error?.localizedDescription ?? "unknown")")
        }
        frame += 1
    }
}
input.markAsFinished()
let videoDone = DispatchSemaphore(value: 0)
writer.finishWriting { videoDone.signal() }
videoDone.wait()
guard writer.status == .completed else {
    fatalError("Video writer failed: \(writer.error?.localizedDescription ?? "unknown")")
}

let composition = AVMutableComposition()
let videoAsset = AVURLAsset(url: silentURL)
let audioAsset = AVURLAsset(url: audioURL)
guard let sourceVideo = videoAsset.tracks(withMediaType: .video).first,
      let sourceAudio = audioAsset.tracks(withMediaType: .audio).first,
      let videoTrack = composition.addMutableTrack(
        withMediaType: .video,
        preferredTrackID: kCMPersistentTrackID_Invalid
      ),
      let audioTrack = composition.addMutableTrack(
        withMediaType: .audio,
        preferredTrackID: kCMPersistentTrackID_Invalid
      ) else { fatalError("Cannot create composition tracks") }

try videoTrack.insertTimeRange(
    CMTimeRange(start: .zero, duration: videoAsset.duration),
    of: sourceVideo,
    at: .zero
)
try audioTrack.insertTimeRange(
    CMTimeRange(start: .zero, duration: audioAsset.duration),
    of: sourceAudio,
    at: .zero
)

guard let exporter = AVAssetExportSession(
    asset: composition,
    presetName: AVAssetExportPreset1920x1080
) else { fatalError("Cannot create exporter") }
exporter.outputURL = outputURL
exporter.outputFileType = .mp4
exporter.shouldOptimizeForNetworkUse = true
let exportDone = DispatchSemaphore(value: 0)
exporter.exportAsynchronously { exportDone.signal() }
exportDone.wait()
guard exporter.status == .completed else {
    fatalError("Export failed: \(exporter.error?.localizedDescription ?? "unknown")")
}

print(outputURL.path)
