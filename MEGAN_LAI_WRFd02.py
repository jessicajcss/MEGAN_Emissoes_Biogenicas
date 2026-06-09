// ==============================
// MEGAN proxy LAI for WRF d02
// Source: MODIS MCD15A3H.061 LAI
// Output: 12 monthly climatology GeoTIFFs clipped to exact WRF d02 polygon
// ==============================

// ------------------------------
// 1) USER SETTINGS
// ------------------------------

// Replace with your uploaded asset/table containing the exact WRF d02 polygon.
// Example asset path after upload in GEE:
// var wrfDomainFc = ee.FeatureCollection('projects/ee-your_user/assets/wrf_d02_polygon');
var wrfDomainFc = ee.FeatureCollection('projects/ee-jessicajcss/assets/wrf_d02_polygon');

// Time span for climatology.
// For your first test, keep a broad climatology to avoid unstable 2-day behavior.
// Later you can change to year-specific monthly means.
var startDate = '2019-01-01';
var endDate   = '2020-12-31';

// Export settings
var exportFolder = 'GEE_MEGAN_LAI_SC_Brazil';
var exportScale = 500;  // MCD15A3H nominal pixel size
var crsOut = 'EPSG:4326';

// ------------------------------
// 2) DOMAIN GEOMETRY
// ------------------------------
var wrfGeom = wrfDomainFc.geometry();
Map.centerObject(wrfGeom, 7);
Map.addLayer(wrfGeom, {color: 'red'}, 'WRF d02 polygon');

// ------------------------------
// 3) MODIS LAI COLLECTION
// ------------------------------
// MODIS/061/MCD15A3H
// LAI scale factor = 0.1
var modisLai = ee.ImageCollection('MODIS/061/MCD15A3H')
  .filterDate(startDate, endDate)
  .filterBounds(wrfGeom)
  .select(['Lai', 'FparLai_QC'])
  .map(function(img) {
    var lai = img.select('Lai').multiply(0.1).rename('LAI');
    
    // Conservative QA mask:
    // keep pixels where QC band exists; for first-pass proxy we avoid aggressive masking.
    // You can tighten this later after validation.
    var qc = img.select('FparLai_QC');
    var masked = lai.updateMask(qc.gte(0));
    
    return masked
      .copyProperties(img, ['system:time_start']);
  });

print('MODIS LAI collection size', modisLai.size());
print('First image', modisLai.first());

// Quick visualization
var laiVis = {
  min: 0,
  max: 6,
  palette: ['f7fcf5', 'c7e9c0', '74c476', '238b45', '00441b']
};
Map.addLayer(modisLai.mean().clip(wrfGeom), laiVis, 'Mean LAI');

// ------------------------------
// 4) MONTHLY CLIMATOLOGY
// ------------------------------
var months = ee.List.sequence(1, 12);

var monthlyClimatology = ee.ImageCollection.fromImages(
  months.map(function(m) {
    m = ee.Number(m);
    var monthly = modisLai
      .filter(ee.Filter.calendarRange(m, m, 'month'))
      .mean()
      .clip(wrfGeom)
      .set('month', m)
      .set('system:index', ee.String('month_').cat(m.format('%02d')))
      .set('description', ee.String('MODIS_MCD15A3H_LAI_month_').cat(m.format('%02d')));
    return monthly;
  })
);

print('Monthly climatology', monthlyClimatology);

// ------------------------------
// 5) OPTIONAL YEAR-SPECIFIC MONTHLY MEANS
// ------------------------------
// Keep this block for later full-year runs.
// Example usage: set targetYear = 2020 and export Jan-Dec 2020 means.
var targetYear = 2020;

var monthlyYearSpecific = ee.ImageCollection.fromImages(
  months.map(function(m) {
    m = ee.Number(m);
    var monthly = modisLai
      .filter(ee.Filter.calendarRange(targetYear, targetYear, 'year'))
      .filter(ee.Filter.calendarRange(m, m, 'month'))
      .mean()
      .clip(wrfGeom)
      .set('month', m)
      .set('year', targetYear)
      .set('system:index', ee.String('Y').cat(ee.Number(targetYear).format())
        .cat('_M').cat(m.format('%02d')))
      .set('description', ee.String('MODIS_MCD15A3H_LAI_')
        .cat(ee.Number(targetYear).format())
        .cat('_')
        .cat(m.format('%02d')));
    return monthly;
  })
);

print('Year-specific monthly means', monthlyYearSpecific);

// ------------------------------
// 6) EXPORT MONTHLY CLIMATOLOGY
// ------------------------------
months.getInfo().forEach(function(m) {
  var img = ee.Image(
    monthlyClimatology.filter(ee.Filter.eq('month', m)).first()
  );

  var monthStr = ('0' + m).slice(-2);

  Export.image.toDrive({
    image: img,
    description: 'SCB_LAI_CLIM_' + monthStr,
    folder: exportFolder,
    fileNamePrefix: 'SCB_LAI_CLIM_' + monthStr,
    region: wrfGeom,
    scale: exportScale,
    crs: crsOut,
    maxPixels: 1e13
  });
});

// ------------------------------
// 7) OPTIONAL EXPORT YEAR-SPECIFIC MONTHLY FILES
// ------------------------------
// Uncomment this block later when you move to full-year workflows.
/*
months.getInfo().forEach(function(m) {
  var img = ee.Image(
    monthlyYearSpecific.filter(ee.Filter.eq('month', m)).first()
  );

  var monthStr = ('0' + m).slice(-2);

  Export.image.toDrive({
    image: img,
    description: 'SCB_LAI_' + targetYear + '_' + monthStr,
    folder: exportFolder,
    fileNamePrefix: 'SCB_LAI_' + targetYear + '_' + monthStr,
    region: wrfGeom,
    scale: exportScale,
    crs: crsOut,
    maxPixels: 1e13
  });
});
*/

// ------------------------------
// 8) OPTIONAL DOMAIN MEAN TIME SERIES CHECK
// ------------------------------
var domainTs = modisLai.map(function(img) {
  var stat = img.reduceRegion({
    reducer: ee.Reducer.mean(),
    geometry: wrfGeom,
    scale: exportScale,
    maxPixels: 1e13
  });
  return ee.Feature(null, {
    date: ee.Date(img.get('system:time_start')).format('YYYY-MM-dd'),
    lai_mean: stat.get('LAI')
  });
});

print('Domain LAI time series sample', domainTs.limit(10));